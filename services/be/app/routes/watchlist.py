"""
Watchlist and Market Data Routes

API endpoints for watchlist management, option chains, and expiry dates.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
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


@router.get("/search")
async def search_tickers(
    q: str = Query(..., min_length=1, description="Search query for symbol or name"),
    limit: int = Query(10, ge=1, le=50),
    svc: MarketDataService = Depends(get_market_data_service),
):
    """Search available tickers by symbol or name."""
    return await svc.search_tickers(DEFAULT_USER_ID, q, limit)


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


# WebSocket endpoint for real-time option chain streaming
@option_chain_router.websocket("/stream")
async def option_chain_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time option chain streaming

    **Usage:**
    1. Connect to ws://host/api/option-chain/stream
    2. Send JSON: {"symbol": "NIFTY", "expiry": "2026-03-05"}
    3. Receive real-time option chain updates every second
    4. Send new symbol/expiry to change subscription

    **Message Format:**
    - Subscribe: {"symbol": "NIFTY", "expiry": "2026-03-05"}
    - Response: {"type": "option_chain", "data": {...}}
    """
    await websocket.accept()

    current_symbol = None
    current_expiry = None

    try:
        # Get services from app state
        from app.database import async_session_factory

        while True:
            # Check for incoming messages (non-blocking)
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                data = json.loads(message)

                # Update subscription
                current_symbol = data.get("symbol")
                current_expiry = data.get("expiry")

                logger.info(f"WebSocket subscribed to {current_symbol} expiry {current_expiry}")

                await websocket.send_json({
                    "type": "subscribed",
                    "symbol": current_symbol,
                    "expiry": current_expiry
                })

            except asyncio.TimeoutError:
                pass  # No message received, continue to send updates
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue

            # Send option chain updates if subscribed
            if current_symbol:
                try:
                    async with async_session_factory() as session:
                        # Get option chain using MarketDataService
                        price_service = getattr(websocket.app.state, "price_service", None)
                        svc = MarketDataService(session, price_service)
                        option_chain = await svc.get_option_chain(current_symbol.upper(), current_expiry)

                        # Log strike count for debugging
                        strike_count = len(option_chain.get("strikes", [])) if option_chain else 0
                        logger.info(f"Sending {strike_count} strikes for {current_symbol} at spot {option_chain.get('spot_price') if option_chain else 'N/A'}")

                        await websocket.send_json({
                            "type": "option_chain",
                            "data": option_chain,
                            "timestamp": asyncio.get_event_loop().time()
                        })

                except Exception as e:
                    logger.error(f"Error fetching option chain: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            # Wait 2 seconds before next update
            await asyncio.sleep(2.0)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {current_symbol}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


# WebSocket endpoint for real-time watchlist price streaming
@router.websocket("/stream")
async def watchlist_price_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time watchlist price streaming

    **Usage:**
    1. Connect to ws://host/api/watchlist/stream
    2. Automatically streams price updates for all watchlist items
    3. Receive updates every 2 seconds

    **Message Format:**
    - Response: {"type": "prices", "data": {"NIFTY": 25100.50, "RELIANCE": 1280.30, ...}}
    """
    await websocket.accept()

    try:
        from app.database import async_session_factory

        logger.info("Watchlist WebSocket connected")

        while True:
            try:
                async with async_session_factory() as session:
                    # Get watchlist items
                    price_service = getattr(websocket.app.state, "price_service", None)
                    svc = MarketDataService(session, price_service)
                    watchlist = await svc.get_watchlist(DEFAULT_USER_ID)

                    if watchlist and len(watchlist) > 0:
                        # Build price update map
                        price_updates = {}
                        for item in watchlist:
                            symbol = item.get("symbol") if isinstance(item, dict) else getattr(item, "symbol", None)
                            if symbol:
                                price_updates[symbol] = {
                                    "price": item.get("price", 0) if isinstance(item, dict) else getattr(item, "price", 0),
                                    "change": item.get("change", 0) if isinstance(item, dict) else getattr(item, "change", 0),
                                    "change_percent": item.get("change_percent", 0) if isinstance(item, dict) else getattr(item, "change_percent", 0),
                                    "high": item.get("high") if isinstance(item, dict) else getattr(item, "high", None),
                                    "low": item.get("low") if isinstance(item, dict) else getattr(item, "low", None),
                                }

                        if price_updates:
                            await websocket.send_json({
                                "type": "prices",
                                "data": price_updates,
                                "timestamp": asyncio.get_event_loop().time()
                            })

                            logger.debug(f"Sent price updates for {len(price_updates)} symbols")
                    else:
                        logger.debug("No watchlist items to stream")

            except WebSocketDisconnect:
                # Client disconnected, break the loop
                raise
            except Exception as e:
                logger.error(f"Error fetching watchlist prices: {e}", exc_info=True)
                # Don't try to send error if connection is already closed
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    # Connection already closed, break the loop
                    raise WebSocketDisconnect()

            # Wait 2 seconds before next update
            await asyncio.sleep(2.0)

    except WebSocketDisconnect:
        logger.info("Watchlist WebSocket disconnected")
    except Exception as e:
        logger.error(f"Watchlist WebSocket error: {e}", exc_info=True)
