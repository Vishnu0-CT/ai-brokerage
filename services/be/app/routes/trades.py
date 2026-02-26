"""
Trade History Routes

API endpoints for trade history, analytics, and behavioral pattern detection.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.trade_history import TradeHistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trades", tags=["trades"])


def get_trade_history_service(
    session: AsyncSession = Depends(get_session),
) -> TradeHistoryService:
    return TradeHistoryService(session)


@router.get("")
async def get_trades(
    days: int | None = Query(None, description="Filter trades from last N days"),
    strategy: str | None = Query(None, description="Filter by strategy name"),
    instrument: str | None = Query(None, description="Filter by instrument (partial match)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of trades to return"),
    offset: int = Query(0, ge=0, description="Number of trades to skip"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Get trade history with optional filters and pagination."""
    return await svc.get_trades(
        user_id=DEFAULT_USER_ID,
        days=days,
        strategy=strategy,
        instrument=instrument,
        limit=limit,
        offset=offset,
    )


@router.get("/analytics")
async def get_analytics(
    days: int | None = Query(None, description="Calculate analytics for last N days"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Get comprehensive trading analytics."""
    return await svc.calculate_analytics(DEFAULT_USER_ID, days=days)


@router.get("/strategy-performance")
async def get_strategy_performance(
    days: int | None = Query(None, description="Calculate for last N days"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Get performance breakdown by strategy."""
    return await svc.get_strategy_performance(DEFAULT_USER_ID, days=days)


@router.get("/weekly-pnl")
async def get_weekly_pnl(
    weeks: int = Query(10, description="Number of weeks to include"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Get weekly P&L trends."""
    return await svc.get_weekly_pnl(DEFAULT_USER_ID, weeks=weeks)


@router.get("/detect/revenge")
async def detect_revenge_trading(
    lookback: int = Query(10, description="Number of recent trades to analyze"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Detect revenge trading patterns in recent trades."""
    return await svc.detect_revenge_trade(DEFAULT_USER_ID, lookback_trades=lookback)


@router.get("/detect/overtrading")
async def detect_overtrading(
    threshold: int = Query(20, description="Trades per day threshold"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Detect overtrading days and their impact."""
    return await svc.detect_overtrading(DEFAULT_USER_ID, threshold=threshold)


@router.get("/summary")
async def get_trade_summary_for_ai(
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """Get comprehensive trade summary formatted for AI system prompt."""
    return await svc.get_trade_summary_for_ai(DEFAULT_USER_ID)


@router.post("/generate")
async def generate_trade_history(
    days: int = Query(65, description="Number of days of history to generate"),
    force: bool = Query(False, description="Force regeneration even if trades exist"),
    svc: TradeHistoryService = Depends(get_trade_history_service),
):
    """
    Generate mock trade history with behavioral patterns.
    
    By default, this endpoint will not generate trades if history already exists.
    Use force=true to regenerate (existing trades will be preserved, new ones added).
    """
    # Check if trades already exist
    existing_result = await svc.get_trades(DEFAULT_USER_ID, days=1, limit=1)
    
    if existing_result["total"] > 0 and not force:
        all_trades_result = await svc.get_trades(DEFAULT_USER_ID, limit=1)
        return {
            "success": False,
            "error": "Trade history already exists. Use force=true to add more trades.",
            "existing_trades": all_trades_result["total"],
            "trades_generated": 0,
        }
    
    count = await svc.generate_and_save_history(DEFAULT_USER_ID, days=days)
    return {"success": True, "trades_generated": count}
