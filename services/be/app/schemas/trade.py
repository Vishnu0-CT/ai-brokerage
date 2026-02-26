from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TradeBase(BaseModel):
    instrument: str
    trade_type: str  # "BUY" or "SELL"
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    strategy: str
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class TradeCreate(TradeBase):
    date: datetime
    time: str
    pnl: Decimal
    pnl_percent: Decimal
    hold_time_minutes: int
    is_revenge_trade: bool = False
    is_overtrade: bool = False
    is_tilt_trade: bool = False


class TradeResponse(TradeBase):
    id: str
    date: datetime
    time: str
    pnl: Decimal
    pnl_percent: Decimal
    hold_time_minutes: int
    is_revenge_trade: bool
    is_overtrade: bool
    is_tilt_trade: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TradeAnalytics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: Decimal
    avg_pnl: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    max_win: Decimal
    max_loss: Decimal
    profit_factor: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    max_drawdown: Decimal
    max_drawdown_percent: float
    sharpe_ratio: float
    
    # Behavioral stats
    revenge_trade_count: int
    revenge_trade_loss: Decimal
    overtrade_days: int
    overtrade_impact: Decimal
    tilt_trade_count: int
    tilt_trade_loss: Decimal
    
    # Time-based stats
    best_trading_hour: str
    worst_trading_hour: str
    best_trading_day: str
    worst_trading_day: str


class StrategyPerformance(BaseModel):
    strategy: str
    trades: int
    win_rate: float
    avg_pnl: Decimal
    total_pnl: Decimal


class WeeklyPnL(BaseModel):
    week_start: str
    week_end: str
    pnl: Decimal
    trades: int
    win_rate: float


class TradeSummaryForAI(BaseModel):
    """Summary data formatted for AI system prompt."""
    overall_stats: TradeAnalytics
    strategy_performance: list[StrategyPerformance]
    weekly_pnl: list[WeeklyPnL]
    recent_patterns: dict  # Detected behavioral patterns
    risk_metrics: dict


class PositionCreate(BaseModel):
    symbol: str
    position_type: str  # "BUY" or "SELL"
    quantity: int
    lots: int
    avg_price: Decimal
    expiry: str


class PositionResponse(BaseModel):
    id: str
    symbol: str
    position_type: str
    quantity: int
    lots: int
    avg_price: Decimal
    ltp: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    pnl_percent: Optional[float] = None
    expiry: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExitPositionRequest(BaseModel):
    exit_price: Optional[Decimal] = None  # If not provided, use current market price
