from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Transaction
from app.models.portfolio import Holding, PortfolioConfig
from app.services.exceptions import InsufficientFundsError, InsufficientHoldingsError


class OrderService:
    def __init__(self, session: AsyncSession, margin_service: Any = None) -> None:
        self._session = session
        self._margin = margin_service

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

        buying_power_info: dict | None = None
        if self._margin:
            buying_power_info = await self._margin.get_buying_power(user_id)
            if buying_power_info["buying_power"] < float(cost):
                raise InsufficientFundsError(float(cost), buying_power_info["buying_power"])
        elif config.current_cash < cost:
            raise InsufficientFundsError(float(cost), float(config.current_cash))

        config.current_cash -= cost

        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()

        if holding is None:
            holding = Holding(
                user_id=user_id, symbol=symbol,
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
        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()

        if holding is None or holding.quantity < quantity:
            available = float(holding.quantity) if holding else 0
            raise InsufficientHoldingsError(symbol, float(quantity), available)

        proceeds = quantity * price

        holding.quantity -= quantity
        if holding.quantity == 0:
            await self._session.delete(holding)

        cfg_result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = cfg_result.scalar_one()
        config.current_cash += proceeds

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
