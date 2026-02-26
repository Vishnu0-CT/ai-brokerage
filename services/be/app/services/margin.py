from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import MarginConfig, PortfolioConfig


class MarginService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_config(self, user_id: uuid.UUID) -> MarginConfig:
        result = await self._session.execute(
            select(MarginConfig).where(MarginConfig.user_id == user_id)
        )
        config = result.scalar_one_or_none()
        if config is None:
            config = MarginConfig(
                user_id=user_id,
                margin_multiplier=Decimal("1.0"),
                maintenance_margin_pct=Decimal("25.0"),
            )
            self._session.add(config)
            await self._session.commit()
            await self._session.refresh(config)
        return config

    async def get_buying_power(self, user_id: uuid.UUID) -> dict:
        margin_cfg = await self.get_or_create_config(user_id)
        result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        portfolio_cfg = result.scalar_one()

        cash = portfolio_cfg.current_cash
        multiplier = margin_cfg.margin_multiplier
        buying_power = cash * multiplier

        return {
            "buying_power": float(buying_power),
            "margin_multiplier": float(multiplier),
            "maintenance_margin_pct": float(margin_cfg.maintenance_margin_pct),
        }

    async def check_maintenance(
        self,
        user_id: uuid.UUID,
        total_value: float,
        invested_value: float,
    ) -> dict:
        margin_cfg = await self.get_or_create_config(user_id)
        maintenance_pct = float(margin_cfg.maintenance_margin_pct) / 100

        equity = total_value  # cash + holdings market value
        maintenance_required = invested_value * maintenance_pct
        margin_call = equity < maintenance_required

        return {
            "equity": round(equity, 2),
            "maintenance_required": round(maintenance_required, 2),
            "margin_call": margin_call,
            "excess_margin": round(equity - maintenance_required, 2),
        }
