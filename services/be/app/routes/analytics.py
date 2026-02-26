from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_analytics_service(
    request: Request, session: AsyncSession = Depends(get_session),
) -> AnalyticsService:
    return AnalyticsService(session, request.app.state.price_service)


@router.get("/coaching")
async def get_coaching_insights(
    period: str = Query("1m"),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_coaching_insights(DEFAULT_USER_ID, period)


@router.get("/win-rate-by-time")
async def get_win_rate_by_time(
    period: str = Query("1m"),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_win_rate_by_time(DEFAULT_USER_ID, period)


@router.get("/instrument-stats")
async def get_instrument_stats(
    period: str = Query("1m"),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_instrument_stats(DEFAULT_USER_ID, period)


@router.get("/trades")
async def filter_trades(
    instrument: str | None = Query(None),
    direction: str | None = Query(None),
    date_range_start: str | None = Query(None),
    date_range_end: str | None = Query(None),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    date_range = None
    if date_range_start and date_range_end:
        date_range = (
            datetime.fromisoformat(date_range_start),
            datetime.fromisoformat(date_range_end),
        )
    return await svc.filter_trades(
        DEFAULT_USER_ID, instrument=instrument,
        date_range=date_range, direction=direction,
    )


@router.get("/metrics")
async def aggregate_metrics(
    metric: str = Query("pnl"),
    group_by: str | None = Query(None),
    instrument: str | None = Query(None),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    filter_params = {}
    if instrument:
        filter_params["instrument"] = instrument
    return await svc.aggregate_metrics(
        DEFAULT_USER_ID, group_by=group_by, metric=metric,
        filter_params=filter_params if filter_params else None,
    )


@router.get("/exposure")
async def calculate_exposure(
    by: str = Query("instrument"),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.calculate_exposure(DEFAULT_USER_ID, by=by)


@router.post("/simulate")
async def simulate_scenario(
    body: dict,
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.simulate_scenario(
        DEFAULT_USER_ID,
        symbol=body.get("symbol"),
        price_change=body.get("price_change"),
        price_change_points=body.get("price_change_points"),
        iv_change=body.get("iv_change"),
        time_decay_days=body.get("time_decay_days"),
        correlations=body.get("correlations", True),
    )


@router.get("/trade-patterns")
async def analyze_trade_patterns(
    event_type: str = Query("after_loss"),
    lookback_count: int = Query(50),
    min_loss_amount: float | None = Query(None),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.analyze_post_event_trades(
        DEFAULT_USER_ID, event_type=event_type,
        lookback_count=lookback_count, min_loss_amount=min_loss_amount,
    )


@router.get("/trading-signal")
async def get_trading_signal(
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.compute_trading_readiness(DEFAULT_USER_ID)
