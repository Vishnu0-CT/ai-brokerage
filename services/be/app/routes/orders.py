from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.order import ConditionCreate, OrderCreate
from app.seed import DEFAULT_USER_ID
from app.services.alert_detector import AlertDetectorService
from app.services.analytics import AnalyticsService
from app.services.condition import ConditionService
from app.services.exceptions import ConditionNotFoundError
from app.services.margin import MarginService
from app.services.order import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


def get_order_service(
    request: Request, session: AsyncSession = Depends(get_session),
) -> OrderService:
    margin_svc = MarginService(session)
    return OrderService(session=session, margin_service=margin_svc)


def get_condition_service(
    request: Request, session: AsyncSession = Depends(get_session),
) -> ConditionService:
    return ConditionService(
        session=session,
        price_service=request.app.state.price_service,
        order_service=OrderService(session=session),
        price_monitor=request.app.state.price_monitor,
        scheduler_service=request.app.state.scheduler_service,
    )


@router.get("")
async def get_transactions(
    symbol: str | None = None,
    side: str | None = None,
    svc: OrderService = Depends(get_order_service),
):
    return await svc.get_transactions(DEFAULT_USER_ID, symbol=symbol, side=side)


@router.post("")
async def place_order(
    body: OrderCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    margin_svc = MarginService(session)
    order_svc = OrderService(session=session, margin_service=margin_svc)
    result = await order_svc.place_order(
        user_id=DEFAULT_USER_ID,
        symbol=body.symbol,
        side=body.side,
        quantity=body.quantity,
        price=body.price,
    )

    # Trigger alert detection after order placement
    try:
        analytics_svc = AnalyticsService(session, request.app.state.price_service)
        alert_svc = AlertDetectorService(session, analytics_svc)
        await alert_svc.evaluate_all(DEFAULT_USER_ID)
    except Exception:
        logger.warning("Alert detection after order failed", exc_info=True)

    return result


@router.get("/conditions")
async def get_active_conditions(
    svc: ConditionService = Depends(get_condition_service),
):
    conditions = await svc.get_active(DEFAULT_USER_ID)
    return [
        {
            "id": str(c.id),
            "condition_type": c.condition_type,
            "parameters": c.parameters,
            "action": c.action,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        }
        for c in conditions
    ]


@router.post("/conditions")
async def create_condition(
    body: ConditionCreate,
    request: Request,
    svc: ConditionService = Depends(get_condition_service),
):
    condition = await svc.create(
        user_id=DEFAULT_USER_ID,
        condition_type=body.condition_type,
        parameters=body.parameters,
        action=body.action,
    )

    # Wire into monitoring
    price_monitor = request.app.state.price_monitor
    scheduler_service = request.app.state.scheduler_service

    if condition.condition_type in ("price_above", "price_below", "portfolio_drawdown", "portfolio_concentration"):
        price_monitor.watch(condition)
    elif condition.condition_type in ("time_at", "time_after"):
        from datetime import datetime
        target = datetime.fromisoformat(condition.parameters["datetime"])
        await scheduler_service.schedule_once(condition, run_at=target)

    return {
        "id": str(condition.id),
        "condition_type": condition.condition_type,
        "parameters": condition.parameters,
        "action": condition.action,
        "status": condition.status,
        "created_at": condition.created_at.isoformat(),
    }


@router.delete("/conditions/{condition_id}")
async def cancel_condition(
    condition_id: uuid.UUID,
    svc: ConditionService = Depends(get_condition_service),
):
    try:
        await svc.cancel(condition_id)
        return {"status": "cancelled"}
    except ConditionNotFoundError:
        raise HTTPException(status_code=404, detail="Condition not found")
