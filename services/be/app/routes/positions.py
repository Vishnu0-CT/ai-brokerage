"""
Position Routes

API endpoints for position management, order placement, and exit functionality.
"""
from __future__ import annotations

import logging
import re
import uuid
from decimal import Decimal
from enum import Enum
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.position_service import PositionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/positions", tags=["positions"])


def get_position_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> PositionService:
    price_service = getattr(request.app.state, "price_service", None)
    return PositionService(session, price_service)


# Request models with validation
class OrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=100, description="e.g., 'NIFTY 26500 CE'")
    order_type: Literal["BUY", "SELL"] = Field(..., description="Order type: BUY or SELL")
    quantity: int = Field(..., gt=0, description="Total quantity (must be positive)")
    lots: int = Field(..., gt=0, description="Number of lots (must be positive)")
    price: Decimal = Field(..., gt=0, description="Price per unit (must be positive)")
    expiry: str = Field(..., min_length=1, description="Expiry date")
    
    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        v = v.strip().upper()
        if not v:
            raise ValueError("Symbol cannot be empty")
        # Basic format check: should contain letters and optionally numbers/spaces
        if not re.match(r'^[A-Z][A-Z0-9\s]+$', v):
            raise ValueError("Invalid symbol format")
        return v
    
    @field_validator("expiry")
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        """Validate expiry date format."""
        v = v.strip()
        # Accept YYYY-MM-DD format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("Expiry must be in YYYY-MM-DD format")
        return v


class ExitPositionRequest(BaseModel):
    exit_price: Decimal | None = None


@router.get("")
async def get_positions(
    svc: PositionService = Depends(get_position_service),
):
    """Get all open positions with current P&L."""
    return await svc.get_positions(DEFAULT_USER_ID)


@router.get("/summary")
async def get_position_summary(
    svc: PositionService = Depends(get_position_service),
):
    """Get summary of all positions."""
    return await svc.get_position_summary(DEFAULT_USER_ID)


@router.post("")
async def place_order(
    body: OrderRequest,
    svc: PositionService = Depends(get_position_service),
):
    """Place an order and create a position."""
    return await svc.place_order(
        user_id=DEFAULT_USER_ID,
        symbol=body.symbol,
        order_type=body.order_type,
        quantity=body.quantity,
        lots=body.lots,
        price=body.price,
        expiry=body.expiry,
    )


@router.get("/{position_id}")
async def get_position(
    position_id: uuid.UUID,
    svc: PositionService = Depends(get_position_service),
):
    """Get a specific position by ID."""
    position = await svc.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/{position_id}/exit")
async def exit_position(
    position_id: uuid.UUID,
    body: ExitPositionRequest | None = None,
    svc: PositionService = Depends(get_position_service),
):
    """Exit a position and record the trade."""
    exit_price = body.exit_price if body else None
    result = await svc.exit_position(position_id, exit_price)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to exit position"))
    
    return result


@router.post("/exit-all")
async def exit_all_positions(
    svc: PositionService = Depends(get_position_service),
):
    """Exit all open positions."""
    return await svc.exit_all_positions(DEFAULT_USER_ID)
