from __future__ import annotations

from pydantic import BaseModel


class HoldingResponse(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float | None = None
    pnl: float
    pnl_pct: float
    lots: int | None = None
    expiry: str | None = None
    created_at: str | None = None


class PortfolioBalanceResponse(BaseModel):
    cash: float
    initial_cash: float
    invested_value: float
    total_value: float
    total_pnl: float
