from __future__ import annotations

from pydantic import BaseModel


class HoldingResponse(BaseModel):
    symbol: str
    side: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float | None = None
    pnl: float
    pnl_pct: float


class PortfolioBalanceResponse(BaseModel):
    cash: float
    initial_cash: float
    invested_value: float
    total_value: float
    total_pnl: float
