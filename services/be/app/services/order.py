from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Transaction
from app.models.portfolio import Holding, PortfolioConfig
from app.models.trade import Trade
from app.services.exceptions import InsufficientFundsError, InsufficientHoldingsError


class OrderService:
    def __init__(self, session: AsyncSession, margin_service: Any = None, price_service: Any = None) -> None:
        self._session = session
        self._margin = margin_service
        self._price_service = price_service

    async def place_order(
        self,
        user_id: uuid.UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        triggered_by: uuid.UUID | None = None,
    ) -> dict:
        if side == "buy":
            return await self._buy(user_id, symbol, quantity, price, triggered_by)
        elif side == "sell":
            return await self._sell(user_id, symbol, quantity, price, triggered_by)
        else:
            raise ValueError(f"Invalid side: {side}")

    async def _buy(
        self, user_id: uuid.UUID, symbol: str,
        quantity: Decimal, price: Decimal, triggered_by: uuid.UUID | None,
    ) -> dict:
        cost = quantity * price

        cfg_result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = cfg_result.scalar_one()

        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()

        buying_power_info: dict | None = None

        if holding and holding.side == "short":
            # Closing/reducing a short — pay to buy back
            if quantity > holding.quantity:
                raise InsufficientHoldingsError(symbol, float(quantity), float(holding.quantity))
            config.current_cash -= cost
            holding.quantity -= quantity
            if holding.quantity == 0:
                await self._session.delete(holding)
        else:
            # Opening/adding to a long — spend cash
            if self._margin:
                buying_power_info = await self._margin.get_buying_power(user_id)
                if buying_power_info["buying_power"] < float(cost):
                    raise InsufficientFundsError(float(cost), buying_power_info["buying_power"])
            elif config.current_cash < cost:
                raise InsufficientFundsError(float(cost), float(config.current_cash))

            config.current_cash -= cost

            if holding is None:
                holding = Holding(
                    user_id=user_id, symbol=symbol, side="long",
                    quantity=quantity, avg_price=price,
                )
                self._session.add(holding)
            else:
                total_cost = holding.avg_price * holding.quantity + price * quantity
                holding.quantity += quantity
                holding.avg_price = total_cost / holding.quantity

        txn = Transaction(
            user_id=user_id, symbol=symbol, side="buy",
            quantity=quantity, price=price, triggered_by=triggered_by,
        )
        self._session.add(txn)
        await self._session.commit()

        result = {
            "symbol": symbol, "side": "buy",
            "quantity": quantity, "price": price,
            "total_cost": cost,
        }
        if buying_power_info:
            result["buying_power"] = buying_power_info
        return result

    async def _sell(
        self, user_id: uuid.UUID, symbol: str,
        quantity: Decimal, price: Decimal, triggered_by: uuid.UUID | None,
    ) -> dict:
        cfg_result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = cfg_result.scalar_one()

        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()

        proceeds = quantity * price

        if holding and holding.side == "long":
            # Closing/reducing a long
            if quantity > holding.quantity:
                raise InsufficientHoldingsError(symbol, float(quantity), float(holding.quantity))
            config.current_cash += proceeds
            holding.quantity -= quantity
            if holding.quantity == 0:
                await self._session.delete(holding)
        else:
            # Opening/adding to a short — receive sell proceeds
            config.current_cash += proceeds

            if holding is None:
                holding = Holding(
                    user_id=user_id, symbol=symbol, side="short",
                    quantity=quantity, avg_price=price,
                )
                self._session.add(holding)
            else:
                total_cost = holding.avg_price * holding.quantity + price * quantity
                holding.quantity += quantity
                holding.avg_price = total_cost / holding.quantity

        txn = Transaction(
            user_id=user_id, symbol=symbol, side="sell",
            quantity=quantity, price=price, triggered_by=triggered_by,
        )
        self._session.add(txn)
        await self._session.commit()

        result = {
            "symbol": symbol, "side": "sell",
            "quantity": quantity, "price": price,
            "total_proceeds": proceeds,
        }
        if self._margin:
            bp = await self._margin.get_buying_power(user_id)
            result["margin_freed"] = float(proceeds) * bp["margin_multiplier"]
        return result

    async def get_transactions(
        self, user_id: uuid.UUID, symbol: str | None = None,
        side: str | None = None,
    ) -> list[dict]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        if symbol:
            stmt = stmt.where(Transaction.symbol == symbol)
        if side:
            stmt = stmt.where(Transaction.side == side)
        stmt = stmt.order_by(Transaction.created_at.desc())

        result = await self._session.execute(stmt)
        return [
            {
                "id": str(t.id), "symbol": t.symbol, "side": t.side,
                "quantity": t.quantity, "price": t.price,
                "triggered_by": str(t.triggered_by) if t.triggered_by else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in result.scalars().all()
        ]

    async def place_fno_order(
        self,
        user_id: uuid.UUID,
        symbol: str,
        order_type: str,
        quantity: int,
        lots: int,
        price: Decimal,
        expiry: str,
    ) -> dict:
        """Place an F&O order. Delegates to _buy/_sell, then patches F&O fields on the holding."""
        side = "buy" if order_type == "BUY" else "sell"
        await self.place_order(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=Decimal(quantity),
            price=price,
        )

        # Patch F&O-specific fields on the holding
        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one()
        holding.lots = lots
        holding.expiry = expiry
        await self._session.commit()

        return {
            "id": str(holding.id),
            "symbol": holding.symbol,
            "type": order_type,
            "quantity": int(holding.quantity),
            "lots": holding.lots,
            "avg_price": float(holding.avg_price),
            "expiry": holding.expiry,
            "timestamp": holding.created_at.isoformat() if holding.created_at else None,
            "status": "filled",
        }

    async def exit_holding(
        self,
        user_id: uuid.UUID,
        symbol: str,
        exit_price: Decimal | None = None,
    ) -> dict:
        """Exit a holding entirely. Creates a Trade record for analytics."""
        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()
        if not holding:
            raise ValueError(f"No holding found for symbol: {symbol}")

        # Get exit price from price service if not provided
        if exit_price is None:
            if self._price_service:
                tick = await self._price_service.get_price(symbol)
                exit_price = Decimal(str(tick.price)) if tick else holding.avg_price
            else:
                exit_price = holding.avg_price

        qty = holding.quantity
        avg = holding.avg_price
        is_long = holding.side == "long"

        # Calculate P&L
        if is_long:
            pnl = (float(exit_price) - float(avg)) * float(qty)
        else:
            pnl = (float(avg) - float(exit_price)) * float(qty)

        pnl_percent = (pnl / (float(avg) * float(qty))) * 100 if avg * qty else 0

        # Calculate hold time
        hold_time_minutes = 0
        if holding.created_at:
            hold_time = datetime.now(timezone.utc) - holding.created_at
            hold_time_minutes = int(hold_time.total_seconds() / 60)

        # Close the holding via existing _sell/_buy
        if is_long:
            await self._sell(user_id, symbol, qty, exit_price, triggered_by=None)
        else:
            await self._buy(user_id, symbol, qty, exit_price, triggered_by=None)

        # Create Trade record for analytics pipeline
        trade = Trade(
            id=uuid.uuid4(),
            user_id=user_id,
            date=datetime.now(timezone.utc),
            time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            instrument=symbol,
            trade_type="BUY" if is_long else "SELL",
            entry_price=avg,
            exit_price=exit_price,
            quantity=int(qty),
            pnl=Decimal(str(round(pnl, 2))),
            pnl_percent=Decimal(str(round(pnl_percent, 2))),
            hold_time_minutes=hold_time_minutes,
            strategy="Manual Trade",
            tags=["manual_exit"],
            notes="Holding exited manually",
            is_revenge_trade=False,
            is_overtrade=False,
            is_tilt_trade=False,
        )
        self._session.add(trade)
        await self._session.commit()

        return {
            "success": True,
            "trade": {
                "id": str(trade.id),
                "symbol": trade.instrument,
                "type": trade.trade_type,
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price),
                "quantity": trade.quantity,
                "pnl": float(trade.pnl),
                "pnl_percent": float(trade.pnl_percent),
                "hold_time_minutes": trade.hold_time_minutes,
            },
        }

    async def exit_holding_by_id(
        self,
        holding_id: uuid.UUID,
        exit_price: Decimal | None = None,
    ) -> dict:
        """Exit a holding by its ID. Resolves symbol then delegates to exit_holding."""
        h_result = await self._session.execute(
            select(Holding).where(Holding.id == holding_id)
        )
        holding = h_result.scalar_one_or_none()
        if not holding:
            raise ValueError(f"No holding found with id: {holding_id}")
        return await self.exit_holding(holding.user_id, holding.symbol, exit_price)
