from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Condition(BaseModel):
    type: str  # "indicator", "price_action", "time", "volatility"
    indicator: Optional[str] = None  # "RSI", "MACD", "SuperTrend", etc.
    operator: str  # "crosses_above", "crosses_below", "greater_than", etc.
    value: Any  # int, float, or str
    timeframe: str = "15min"  # "5min", "15min", "1hour", "daily"


class StopLoss(BaseModel):
    type: str  # "fixed", "trailing", "atr_based"
    value: float
    unit: str  # "points", "percent", "atr"


class Target(BaseModel):
    type: str  # "fixed", "risk_reward", "trailing"
    value: float
    unit: str  # "points", "percent", "risk_multiple"


class PositionSize(BaseModel):
    type: str = "fixed"  # "fixed", "percent_of_capital", "risk_based"
    value: float = 1  # Number of lots or percentage
    max_risk_percent: Optional[float] = None


class PaperTradingStats(BaseModel):
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_pnl: float = 0.0
    max_drawdown: float = 0.0
    last_trade_date: Optional[str] = None


class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    entry_conditions: list[Condition] = Field(default_factory=list)
    exit_conditions: list[Condition] = Field(default_factory=list)
    stop_loss: Optional[StopLoss] = None
    target: Optional[Target] = None
    position_size: Optional[PositionSize] = None
    max_positions: int = 1


class StrategyCreate(StrategyBase):
    natural_language_input: Optional[str] = None


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    entry_conditions: Optional[list[Condition]] = None
    exit_conditions: Optional[list[Condition]] = None
    stop_loss: Optional[StopLoss] = None
    target: Optional[Target] = None
    position_size: Optional[PositionSize] = None
    max_positions: Optional[int] = None
    natural_language_input: Optional[str] = None


class StrategyResponse(StrategyBase):
    id: str
    status: str
    paper_trading_stats: PaperTradingStats
    natural_language_input: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyParseRequest(BaseModel):
    """Request to parse natural language strategy description."""
    description: str


class StrategyParseResponse(BaseModel):
    """Parsed strategy from natural language."""
    name: str
    description: str
    entry_conditions: list[Condition]
    exit_conditions: list[Condition]
    stop_loss: Optional[StopLoss] = None
    target: Optional[Target] = None
    position_size: Optional[PositionSize] = None
    confidence: float = 0.0  # How confident the AI is in the parsing


class StrategyTemplate(BaseModel):
    """A pre-defined strategy template."""
    id: str
    title: str
    description: str
    template: str  # Natural language template
    category: str
    icon: str


class StrategyCategory(BaseModel):
    """Category of strategy templates."""
    id: str
    name: str
    icon: str
    color: str
    strategies: list[StrategyTemplate]
