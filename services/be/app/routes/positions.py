from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.order import OrderService
from app.services.portfolio import PortfolioService

router = APIRouter(prefix="/api/positions", tags=["positions"])


def get_order_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> OrderService:
    price_service = getattr(request.app.state, "price_service", None)
    margin_service = getattr(request.app.state, "margin_service", None)
    return OrderService(session, margin_service, price_service)


def get_portfolio_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> PortfolioService:
    return PortfolioService(session=session, price_service=request.app.state.price_service)


class OrderRequest(BaseModel):
    symbol: str
    order_type: str
    quantity: int
    lots: int
    price: Decimal
    expiry: str


class ExitPositionRequest(BaseModel):
    exit_price: Decimal | None = None


@router.get("")
async def get_positions(
    svc: PortfolioService = Depends(get_portfolio_service),
):
    """Get all open holdings (unified positions)."""
    return await svc.get_holdings(DEFAULT_USER_ID)


@router.get("/summary")
async def get_position_summary(
    svc: PortfolioService = Depends(get_portfolio_service),
):
    """Get summary of all holdings."""
    return await svc.get_portfolio_summary(DEFAULT_USER_ID)


@router.post("")
async def place_order(
    body: OrderRequest,
    svc: OrderService = Depends(get_order_service),
):
    """Place an F&O order — creates/upserts a holding with cash impact."""
    return await svc.place_fno_order(
        user_id=DEFAULT_USER_ID,
        symbol=body.symbol,
        order_type=body.order_type,
        quantity=body.quantity,
        lots=body.lots,
        price=body.price,
        expiry=body.expiry,
    )


@router.post("/{holding_id}/exit")
async def exit_position(
    holding_id: uuid.UUID,
    body: ExitPositionRequest | None = None,
    svc: OrderService = Depends(get_order_service),
):
    """Exit a holding by its ID."""
    try:
        return await svc.exit_holding_by_id(
            holding_id=holding_id,
            exit_price=body.exit_price if body else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/exit-all")
async def exit_all_positions(
    svc: OrderService = Depends(get_order_service),
    psvc: PortfolioService = Depends(get_portfolio_service),
):
    """Exit all open holdings."""
    holdings = await psvc.get_holdings(DEFAULT_USER_ID)
    results = []
    total_pnl = 0

    for h in holdings:
        result = await svc.exit_holding(
            user_id=DEFAULT_USER_ID,
            symbol=h["symbol"],
        )
        results.append(result)
        if result["success"]:
            total_pnl += result["trade"]["pnl"]

    return {
        "success": True,
        "positions_closed": len(results),
        "total_pnl": round(total_pnl, 2),
        "results": results,
    }
