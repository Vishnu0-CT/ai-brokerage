from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.portfolio import PortfolioService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def get_portfolio_service(
    request: Request, session: AsyncSession = Depends(get_session),
) -> PortfolioService:
    return PortfolioService(session=session, price_service=request.app.state.price_service)


@router.get("/holdings")
async def get_holdings(
    instrument: str | None = Query(None),
    filter: str | None = Query(None),
    svc: PortfolioService = Depends(get_portfolio_service),
):
    holdings = await svc.get_holdings(DEFAULT_USER_ID)

    if instrument:
        holdings = [h for h in holdings if h.get("symbol") == instrument]

    if filter == "profitable":
        holdings = [h for h in holdings if h.get("unrealized_pnl", 0) > 0]
    elif filter == "losing":
        holdings = [h for h in holdings if h.get("unrealized_pnl", 0) < 0]

    return holdings


@router.get("/balance")
async def get_balance(svc: PortfolioService = Depends(get_portfolio_service)):
    return await svc.get_balance(DEFAULT_USER_ID)


@router.get("/summary")
async def get_summary(svc: PortfolioService = Depends(get_portfolio_service)):
    return await svc.get_portfolio_summary(DEFAULT_USER_ID)


@router.get("/history")
async def get_history(
    period: str = Query("1m", pattern="^(1d|1w|1m|3m)$"),
    svc: PortfolioService = Depends(get_portfolio_service),
):
    days = {"1d": 1, "1w": 7, "1m": 30, "3m": 90}[period]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return await svc.get_value_series(DEFAULT_USER_ID, start, end)
