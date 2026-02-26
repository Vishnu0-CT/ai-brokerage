from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.models.order import ConditionalOrder

logger = logging.getLogger(__name__)


class SchedulerService:
    """Wraps APScheduler v3 for time-based conditional orders and periodic tasks."""

    def __init__(
        self,
        session_factory: Any = None,
        price_service: Any = None,
    ) -> None:
        self._session_factory = session_factory
        self._price_service = price_service
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}  # condition_id -> job_id

    async def start(self) -> None:
        self._scheduler.start()

    async def stop(self) -> None:
        self._scheduler.shutdown(wait=False)

    async def schedule_once(
        self, condition: ConditionalOrder, run_at: datetime,
    ) -> None:
        job = self._scheduler.add_job(
            self._execute_condition,
            trigger=DateTrigger(run_date=run_at),
            args=[condition.id],
        )
        self._jobs[str(condition.id)] = job.id

        # Write scheduler_job_id back to the condition
        condition.scheduler_job_id = job.id

    async def schedule_periodic(
        self, callback: Callable, interval_seconds: int, job_id: str | None = None,
    ) -> str:
        job = self._scheduler.add_job(
            callback,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id=job_id,
        )
        return job.id

    async def remove_job(self, condition_id: str) -> None:
        job_id = self._jobs.pop(condition_id, None)
        if job_id:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                logger.warning(f"Job {job_id} not found for removal")

    async def _execute_condition(self, condition_id: uuid.UUID) -> None:
        if not self._session_factory:
            logger.error(f"No session factory — cannot execute condition {condition_id}")
            return

        try:
            async with self._session_factory() as session:
                from sqlalchemy import select
                from app.services.condition import ConditionService
                from app.services.order import OrderService

                result = await session.execute(
                    select(ConditionalOrder).where(ConditionalOrder.id == condition_id)
                )
                condition = result.scalar_one_or_none()
                if condition is None or condition.status != "active":
                    logger.warning(f"Condition {condition_id} not found or not active")
                    return

                condition_svc = ConditionService(
                    session=session,
                    price_service=self._price_service,
                    order_service=OrderService(session=session),
                )
                await condition_svc.execute(condition)
        except Exception:
            logger.exception(f"Scheduled condition {condition_id} execution failed")
        finally:
            self._jobs.pop(str(condition_id), None)

    async def load_time_conditions(self, conditions: list[ConditionalOrder]) -> None:
        for c in conditions:
            if c.condition_type in ("time_at", "time_after"):
                target = datetime.fromisoformat(c.parameters["datetime"])
                await self.schedule_once(c, run_at=target)
