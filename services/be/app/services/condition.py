from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import ConditionalOrder
from app.models.portfolio import PortfolioSnapshot
from app.services.exceptions import ConditionNotFoundError, PriceUnavailableError

logger = logging.getLogger(__name__)


class ConditionService:
    def __init__(
        self,
        session: AsyncSession,
        price_service: Any,
        order_service: Any,
        portfolio_service: Any | None = None,
        price_monitor: Any | None = None,
        scheduler_service: Any | None = None,
    ) -> None:
        self._session = session
        self._price_service = price_service
        self._order_service = order_service
        self._portfolio_service = portfolio_service
        self._price_monitor = price_monitor
        self._scheduler_service = scheduler_service

    async def create(
        self,
        user_id: uuid.UUID,
        condition_type: str,
        parameters: dict,
        action: dict,
    ) -> ConditionalOrder:
        condition = ConditionalOrder(
            user_id=user_id,
            condition_type=condition_type,
            parameters=parameters,
            action=action,
            status="active",
        )
        self._session.add(condition)
        await self._session.commit()
        await self._session.refresh(condition)
        return condition

    async def evaluate(self, condition: ConditionalOrder) -> bool:
        evaluators = {
            "price_above": self._eval_price_above,
            "price_below": self._eval_price_below,
            "time_at": self._eval_time,
            "time_after": self._eval_time,
            "portfolio_drawdown": self._eval_drawdown,
            "portfolio_concentration": self._eval_concentration,
        }

        evaluator = evaluators.get(condition.condition_type)
        if evaluator is None:
            logger.error(f"Unknown condition type: {condition.condition_type}")
            return False

        try:
            return await evaluator(condition)
        except Exception:
            logger.exception(f"Error evaluating condition {condition.id}")
            return False

    async def execute(self, condition: ConditionalOrder) -> dict | None:
        if condition.status != "active":
            return None

        action = condition.action
        try:
            # Alert-only conditions (no trade to place)
            if action.get("type") == "alert":
                result = {
                    "type": "alert",
                    "symbol": action["symbol"],
                    "condition_type": condition.condition_type,
                    "message": f"Alert triggered for {action['symbol']}",
                }
            else:
                result = await self._order_service.place_order(
                    user_id=condition.user_id,
                    symbol=action["symbol"],
                    side=action["side"],
                    quantity=Decimal(str(action["quantity"])),
                    price=Decimal(str(action.get("price", 0))) if action.get("price") else None,
                    triggered_by=condition.id,
                )
            condition.status = "triggered"
            condition.triggered_at = datetime.now(timezone.utc)
            await self._session.commit()
            return result
        except Exception:
            logger.exception(f"Condition {condition.id} execution failed")
            condition.status = "failed"
            await self._session.commit()
            return None

    async def cancel(self, condition_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(ConditionalOrder).where(ConditionalOrder.id == condition_id)
        )
        condition = result.scalar_one_or_none()
        if condition is None:
            raise ConditionNotFoundError(str(condition_id))

        condition.status = "cancelled"
        await self._session.commit()

        # Unwire from monitoring subsystems
        if self._price_monitor:
            self._price_monitor.unwatch(condition)
        if self._scheduler_service:
            await self._scheduler_service.remove_job(str(condition_id))

    async def get_active(self, user_id: uuid.UUID | None = None) -> list[ConditionalOrder]:
        stmt = select(ConditionalOrder).where(ConditionalOrder.status == "active")
        if user_id:
            stmt = stmt.where(ConditionalOrder.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # --- Evaluators ---

    async def _eval_price_above(self, condition: ConditionalOrder) -> bool:
        params = condition.parameters
        tick = await self._price_service.get_price(params["symbol"])
        if tick is None:
            raise PriceUnavailableError(params["symbol"])
        return tick.price > params["threshold"]

    async def _eval_price_below(self, condition: ConditionalOrder) -> bool:
        params = condition.parameters
        tick = await self._price_service.get_price(params["symbol"])
        if tick is None:
            raise PriceUnavailableError(params["symbol"])
        return tick.price < params["threshold"]

    async def _eval_time(self, condition: ConditionalOrder) -> bool:
        params = condition.parameters
        target = datetime.fromisoformat(params["datetime"])
        return datetime.now(timezone.utc) >= target

    async def _eval_drawdown(self, condition: ConditionalOrder) -> bool:
        if not self._portfolio_service:
            return False
        params = condition.parameters
        user_id = condition.user_id
        threshold = params["threshold"]
        window = params.get("window", "session")

        now = datetime.now(timezone.utc)
        if window == "session":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif window == "1d":
            start = now - timedelta(days=1)
        else:  # all_time
            start = datetime(2000, 1, 1, tzinfo=timezone.utc)

        result = await self._session.execute(
            select(func.max(PortfolioSnapshot.total_value))
            .where(PortfolioSnapshot.user_id == user_id)
            .where(PortfolioSnapshot.created_at >= start)
        )
        peak = result.scalar()
        if peak is None or peak == 0:
            return False

        balance = await self._portfolio_service.get_balance(user_id)
        current = Decimal(str(balance["total_value"]))
        drawdown_pct = float((peak - current) / peak * 100)
        return drawdown_pct >= threshold

    async def _eval_concentration(self, condition: ConditionalOrder) -> bool:
        if not self._portfolio_service:
            return False
        params = condition.parameters
        user_id = condition.user_id
        threshold = params["threshold"]
        symbol_filter = params.get("symbol")

        summary = await self._portfolio_service.get_portfolio_summary(user_id)
        for h in summary["holdings"]:
            if symbol_filter and h["symbol"] != symbol_filter:
                continue
            if h["allocation_pct"] >= threshold:
                return True
        return False
