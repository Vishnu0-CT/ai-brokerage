from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Holding, PortfolioConfig, PortfolioSnapshot
from app.services.price import PriceService


class PortfolioService:
    def __init__(self, session: AsyncSession, price_service: PriceService) -> None:
        self._session = session
        self._price_service = price_service

    async def get_balance(self, user_id: uuid.UUID) -> dict:
        result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = result.scalar_one()
        holdings = await self.get_holdings(user_id)

        invested_value = sum(h["current_price"] * float(h["quantity"]) for h in holdings)
        total_value = float(config.current_cash) + invested_value
        total_pnl = total_value - float(config.initial_cash)

        return {
            "cash": config.current_cash,
            "initial_cash": config.initial_cash,
            "invested_value": round(invested_value, 2),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "daily_loss_limit": config.daily_loss_limit,
        }

    async def get_holdings(self, user_id: uuid.UUID) -> list[dict]:
        result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id)
        )
        holdings = result.scalars().all()
        enriched = []

        for h in holdings:
            tick = await self._price_service.get_price(h.symbol)
            current_price = tick.price if tick else float(h.avg_price)
            qty = float(h.quantity)
            avg = float(h.avg_price)

            if h.side == "short":
                unrealized = (avg - current_price) * qty
            else:
                unrealized = (current_price - avg) * qty

            pnl_pct = (unrealized / (avg * qty)) * 100 if avg * qty else 0

            enriched.append({
                "id": str(h.id),
                "symbol": h.symbol,
                "side": h.side,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "current_price": current_price,
                "unrealized_pnl": round(unrealized, 2),
                "realized_pnl": None,
                "pnl": round(unrealized, 2),
                "pnl_pct": round(pnl_pct, 2),
                "lots": h.lots,
                "expiry": h.expiry,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            })

        return enriched

    async def get_portfolio_summary(self, user_id: uuid.UUID) -> dict:
        balance = await self.get_balance(user_id)
        holdings = await self.get_holdings(user_id)

        total = balance["total_value"]
        for h in holdings:
            h["allocation_pct"] = round(
                (h["current_price"] * float(h["quantity"])) / total * 100, 2
            ) if total > 0 else 0

        return {
            "balance": balance,
            "holdings": holdings,
        }

    async def get_value_at(self, user_id: uuid.UUID, date: datetime) -> dict | None:
        result = await self._session.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == user_id)
            .where(PortfolioSnapshot.created_at <= date)
            .order_by(PortfolioSnapshot.created_at.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            return None
        return {
            "total_value": snapshot.total_value,
            "cash": snapshot.cash,
            "invested_value": snapshot.invested_value,
            "timestamp": snapshot.created_at,
        }

    async def get_value_series(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[dict]:
        result = await self._session.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == user_id)
            .where(PortfolioSnapshot.created_at >= start)
            .where(PortfolioSnapshot.created_at <= end)
            .order_by(PortfolioSnapshot.created_at)
        )
        snapshots = result.scalars().all()
        return [
            {
                "total_value": s.total_value,
                "cash": s.cash,
                "invested_value": s.invested_value,
                "timestamp": s.created_at,
            }
            for s in snapshots
        ]

    async def take_snapshot(self, user_id: uuid.UUID) -> PortfolioSnapshot:
        balance = await self.get_balance(user_id)
        snapshot = PortfolioSnapshot(
            user_id=user_id,
            total_value=Decimal(str(balance["total_value"])),
            cash=balance["cash"],
            invested_value=Decimal(str(balance["invested_value"])),
        )
        self._session.add(snapshot)
        await self._session.commit()
        return snapshot
