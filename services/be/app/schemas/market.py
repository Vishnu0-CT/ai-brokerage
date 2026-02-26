from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class WatchlistItemBase(BaseModel):
    symbol: str
    name: str
    instrument_type: str  # "INDEX" or "STOCK"
    lot_size: int
    tick_size: float = 0.05


class WatchlistItemCreate(WatchlistItemBase):
    display_order: int = 0


class WatchlistItemResponse(WatchlistItemBase):
    id: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None

    class Config:
        from_attributes = True


class OptionData(BaseModel):
    ltp: float  # Last traded price
    bid: float
    ask: float
    oi: int  # Open Interest
    iv: float  # Implied Volatility
    volume: int
    change: float
    change_percent: float


class OptionStrike(BaseModel):
    strike: int
    call: OptionData
    put: OptionData


class OptionChainResponse(BaseModel):
    symbol: str
    spot_price: float
    expiry: str
    strikes: list[OptionStrike]


class ExpiryDate(BaseModel):
    date: str  # "2026-02-27"
    label: str  # "27 Feb"
    is_weekly: bool


class OrderRequest(BaseModel):
    symbol: str  # e.g., "NIFTY 26500 CE"
    order_type: str  # "BUY" or "SELL"
    quantity: int  # Total quantity (lots × lot_size)
    lots: int
    price: Decimal
    expiry: str


class OrderResponse(BaseModel):
    id: str
    symbol: str
    order_type: str
    quantity: int
    lots: int
    price: Decimal
    expiry: str
    timestamp: datetime
    status: str = "filled"  # For mock trading, always filled
