from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from app.models.order import ConditionalOrder
from app.services.price import PriceStream, PriceTick

logger = logging.getLogger(__name__)


class PriceMonitor:
    """Subscribes to price ticks and evaluates conditions per symbol."""

    def __init__(
        self,
        stream: PriceStream,
        session_factory: Any,
        price_service: Any,
        notify_callback: Callable | None = None,
    ) -> None:
        self._stream = stream
        self._session_factory = session_factory
        self._price_service = price_service
        self._notify_callback = notify_callback

        # symbol -> {condition_id: ConditionalOrder}
        self._watchlist: dict[str, dict[str, ConditionalOrder]] = {}
        self._lock = asyncio.Lock()

        self._stream.subscribe(self._on_tick)

    def watch(self, condition: ConditionalOrder) -> None:
        symbol = condition.parameters.get("symbol")
        if not symbol:
            # Portfolio-level conditions watch all symbols
            symbol = "__portfolio__"

        if symbol not in self._watchlist:
            self._watchlist[symbol] = {}
            if symbol != "__portfolio__":
                self._stream.add_symbol(symbol)

        self._watchlist[symbol][str(condition.id)] = condition

    def unwatch(self, condition: ConditionalOrder) -> None:
        symbol = condition.parameters.get("symbol", "__portfolio__")
        if symbol in self._watchlist:
            self._watchlist[symbol].pop(str(condition.id), None)
            if not self._watchlist[symbol]:
                del self._watchlist[symbol]
                if symbol != "__portfolio__":
                    self._stream.remove_symbol(symbol)

    def _on_tick(self, tick: PriceTick) -> None:
        # Schedule async evaluation -- can't await in a sync callback
        conditions = list(self._watchlist.get(tick.symbol, {}).values())
        portfolio_conditions = list(self._watchlist.get("__portfolio__", {}).values())
        all_conditions = conditions + portfolio_conditions

        if all_conditions:
            asyncio.create_task(self._evaluate_conditions(all_conditions))

    async def _evaluate_conditions(self, conditions: list[ConditionalOrder]) -> None:
        async with self._lock:
            for condition in conditions:
                if condition.status != "active":
                    self.unwatch(condition)
                    continue

                try:
                    # Fresh session per evaluation cycle -- avoids stale session issues
                    async with self._session_factory() as session:
                        from app.services.condition import ConditionService
                        from app.services.order import OrderService

                        condition_svc = ConditionService(
                            session=session,
                            price_service=self._price_service,
                            order_service=OrderService(session=session),
                        )

                        # Re-fetch condition from DB to get current status (race guard)
                        from sqlalchemy import select
                        result = await session.execute(
                            select(ConditionalOrder).where(ConditionalOrder.id == condition.id)
                        )
                        db_condition = result.scalar_one_or_none()
                        if db_condition is None or db_condition.status != "active":
                            self.unwatch(condition)
                            continue

                        triggered = await condition_svc.evaluate(db_condition)
                        if triggered:
                            exec_result = await condition_svc.execute(db_condition)
                            self.unwatch(condition)

                            if self._notify_callback and exec_result:
                                self._notify_callback({
                                    "type": "condition_triggered",
                                    "condition_id": str(condition.id),
                                    "result": exec_result,
                                })
                except Exception:
                    logger.exception(f"Error evaluating condition {condition.id}")

    async def load_active_conditions(self, conditions: list[ConditionalOrder]) -> None:
        for c in conditions:
            if c.condition_type in ("price_above", "price_below", "portfolio_drawdown", "portfolio_concentration"):
                self.watch(c)
