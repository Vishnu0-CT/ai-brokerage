from __future__ import annotations

from pydantic import BaseModel


class PortfolioBalanceResponse(BaseModel):
    cash: float
    initial_cash: float
    invested_value: float
    total_value: float
    total_pnl: float
