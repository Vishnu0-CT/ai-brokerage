"""
Watchlist and Market Data Routes

API endpoints for watchlist management, option chains, and expiry dates.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


def get_market_data_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> MarketDataService:
    price_service = getattr(request.app.state, "price_service", None)
    return MarketDataService(session, price_service)


# Request models
class WatchlistAddRequest(BaseModel):
    symbol: str
    name: str
    instrument_type: str  # "INDEX" or "STOCK"
    lot_size: int
    tick_size: float = 0.05


@router.get("")
async def get_watchlist(
    svc: MarketDataService = Depends(get_market_data_service),
):
    """Get user's watchlist with current prices."""
    return await svc.get_watchlist(DEFAULT_USER_ID)


@router.post("")
async def add_to_watchlist(
    body: WatchlistAddRequest,
    svc: MarketDataService = Depends(get_market_data_service),
):
    """Add an item to the watchlist."""
    return await svc.add_to_watchlist(
        user_id=DEFAULT_USER_ID,
        symbol=body.symbol,
        name=body.name,
        instrument_type=body.instrument_type,
        lot_size=body.lot_size,
        tick_size=body.tick_size,
    )


@router.delete("/{item_id}")
async def remove_from_watchlist(
    item_id: uuid.UUID,
    svc: MarketDataService = Depends(get_market_data_service),
):
    """Remove an item from the watchlist."""
    success = await svc.remove_from_watchlist(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"success": True}


@router.post("/seed")
async def seed_watchlist(
    force: bool = Query(False, description="Force seeding even if watchlist exists"),
    svc: MarketDataService = Depends(get_market_data_service),
):
    """
    Seed default watchlist items.
    
    By default, this endpoint will not seed if watchlist already has items.
    Use force=true to add items anyway.
    """
    # Check if watchlist already has items
    existing = await svc.get_watchlist(DEFAULT_USER_ID)
    
    if existing and not force:
        return {
            "success": False,
            "error": "Watchlist already has items. Use force=true to add more.",
            "existing_items": len(existing),
            "items_added": 0,
        }
    
    count = await svc.seed_default_watchlist(DEFAULT_USER_ID)
    return {"success": True, "items_added": count}


# Option Chain endpoints
option_chain_router = APIRouter(prefix="/api/option-chain", tags=["option-chain"])


@option_chain_router.get("/{symbol}")
async def get_option_chain(
    symbol: str,
    expiry: str | None = Query(None, description="Expiry date (YYYY-MM-DD)"),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    """Get option chain for a symbol."""
    price_service = getattr(request.app.state, "price_service", None) if request else None
    svc = MarketDataService(session, price_service)
    return await svc.get_option_chain(symbol.upper(), expiry)


# Expiry dates endpoint
expiry_router = APIRouter(prefix="/api/expiries", tags=["expiries"])


@expiry_router.get("")
async def get_expiry_dates(
    weeks: int = Query(4, description="Number of weeks to include"),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    """Get upcoming expiry dates."""
    price_service = getattr(request.app.state, "price_service", None) if request else None
    svc = MarketDataService(session, price_service)
    return svc.get_expiry_dates(weeks)
