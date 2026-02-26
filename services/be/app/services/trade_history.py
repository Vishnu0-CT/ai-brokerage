"""
Trade History Generator Service

Generates realistic mock trade history with embedded behavioral patterns for AI analysis.
Includes revenge trading, overtrading, tilt trading, and other patterns.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade

# Trading instruments
NIFTY_STRIKES = [26000, 26100, 26200, 26300, 26400, 26500, 26600, 26700, 26800, 26900, 27000]
BANKNIFTY_STRIKES = [57000, 57200, 57400, 57600, 57800, 58000, 58200, 58400, 58600, 58800, 59000]
FINNIFTY_STRIKES = [24000, 24100, 24200, 24300, 24400, 24500, 24600, 24700, 24800, 24900, 25000]

STOCK_OPTIONS = {
    "RELIANCE": {"strikes": [1250, 1260, 1270, 1280, 1290, 1300, 1310, 1320], "lot_size": 250},
    "HDFCBANK": {"strikes": [1700, 1720, 1740, 1760, 1780, 1800, 1820, 1840], "lot_size": 550},
    "INFY": {"strikes": [1500, 1520, 1540, 1560, 1580, 1600, 1620, 1640], "lot_size": 300},
    "TCS": {"strikes": [3700, 3750, 3800, 3850, 3900, 3950, 4000], "lot_size": 175},
    "ICICIBANK": {"strikes": [1050, 1060, 1070, 1080, 1090, 1100, 1110, 1120], "lot_size": 700},
    "SBIN": {"strikes": [750, 760, 770, 780, 790, 800, 810, 820], "lot_size": 1500},
    "TATAMOTORS": {"strikes": [700, 710, 720, 730, 740, 750, 760, 770], "lot_size": 575},
}

# 8 Trading strategies
STRATEGIES = [
    "Momentum Breakout",
    "Mean Reversion",
    "Trend Following",
    "Scalping",
    "Straddle/Strangle",
    "Iron Condor",
    "Directional Puts",
    "Expiry Day Special",
]

# Strategy characteristics
STRATEGY_PROFILES = {
    "Momentum Breakout": {"win_rate": 0.55, "avg_hold_min": 45, "avg_pnl_pct": 8.0, "volatility": 0.3},
    "Mean Reversion": {"win_rate": 0.48, "avg_hold_min": 30, "avg_pnl_pct": 5.0, "volatility": 0.25},
    "Trend Following": {"win_rate": 0.52, "avg_hold_min": 90, "avg_pnl_pct": 12.0, "volatility": 0.35},
    "Scalping": {"win_rate": 0.60, "avg_hold_min": 10, "avg_pnl_pct": 2.0, "volatility": 0.15},
    "Straddle/Strangle": {"win_rate": 0.45, "avg_hold_min": 120, "avg_pnl_pct": 15.0, "volatility": 0.4},
    "Iron Condor": {"win_rate": 0.65, "avg_hold_min": 180, "avg_pnl_pct": 6.0, "volatility": 0.2},
    "Directional Puts": {"win_rate": 0.42, "avg_hold_min": 60, "avg_pnl_pct": 10.0, "volatility": 0.35},
    "Expiry Day Special": {"win_rate": 0.50, "avg_hold_min": 20, "avg_pnl_pct": 20.0, "volatility": 0.5},
}

# Time patterns
MORNING_HOURS = [(9, 15), (9, 30), (9, 45), (10, 0), (10, 15), (10, 30)]
MIDDAY_HOURS = [(10, 45), (11, 0), (11, 30), (12, 0), (12, 30), (13, 0), (13, 30)]
AFTERNOON_HOURS = [(14, 0), (14, 30), (15, 0), (15, 15)]


def _generate_instrument() -> tuple[str, int]:
    """Generate a random instrument and its lot size."""
    choice = random.random()
    
    if choice < 0.4:  # 40% NIFTY
        strike = random.choice(NIFTY_STRIKES)
        option_type = random.choice(["CE", "PE"])
        return f"NIFTY {strike} {option_type}", 50
    elif choice < 0.7:  # 30% BANKNIFTY
        strike = random.choice(BANKNIFTY_STRIKES)
        option_type = random.choice(["CE", "PE"])
        return f"BANKNIFTY {strike} {option_type}", 30
    elif choice < 0.8:  # 10% FINNIFTY
        strike = random.choice(FINNIFTY_STRIKES)
        option_type = random.choice(["CE", "PE"])
        return f"FINNIFTY {strike} {option_type}", 40
    else:  # 20% Stock options
        stock = random.choice(list(STOCK_OPTIONS.keys()))
        strike = random.choice(STOCK_OPTIONS[stock]["strikes"])
        option_type = random.choice(["CE", "PE"])
        return f"{stock} {strike} {option_type}", STOCK_OPTIONS[stock]["lot_size"]


def _generate_trade_time(date: datetime, session: str = "random") -> tuple[int, int]:
    """Generate trade time based on session."""
    if session == "morning" or (session == "random" and random.random() < 0.5):
        return random.choice(MORNING_HOURS)
    elif session == "midday" or (session == "random" and random.random() < 0.7):
        return random.choice(MIDDAY_HOURS)
    else:
        return random.choice(AFTERNOON_HOURS)


def _generate_normal_trade(
    date: datetime,
    strategy: str | None = None,
    session: str = "random",
) -> dict[str, Any]:
    """Generate a normal trade with realistic characteristics."""
    if strategy is None:
        strategy = random.choice(STRATEGIES)
    
    profile = STRATEGY_PROFILES[strategy]
    instrument, lot_size = _generate_instrument()
    
    # Determine win/loss
    is_win = random.random() < profile["win_rate"]
    
    # Generate prices
    entry_price = random.uniform(50, 500)
    
    if is_win:
        pnl_pct = random.gauss(profile["avg_pnl_pct"], profile["avg_pnl_pct"] * profile["volatility"])
        pnl_pct = max(0.5, pnl_pct)  # Minimum 0.5% win
    else:
        pnl_pct = -random.gauss(profile["avg_pnl_pct"] * 0.8, profile["avg_pnl_pct"] * profile["volatility"])
        pnl_pct = min(-0.5, pnl_pct)  # Minimum 0.5% loss
    
    exit_price = entry_price * (1 + pnl_pct / 100)
    
    # Calculate P&L
    quantity = lot_size * random.randint(1, 3)
    pnl = (exit_price - entry_price) * quantity
    
    # Hold time
    hold_time = int(random.gauss(profile["avg_hold_min"], profile["avg_hold_min"] * 0.3))
    hold_time = max(5, min(300, hold_time))
    
    # Trade time
    hour, minute = _generate_trade_time(date, session)
    trade_time = f"{hour:02d}:{minute:02d}:{random.randint(0, 59):02d}"
    
    # Tags
    tags = []
    if hour < 11:
        tags.append("morning_trade")
    elif hour < 14:
        tags.append("midday_trade")
    else:
        tags.append("afternoon_trade")
    
    if "Trend" in strategy or "Momentum" in strategy:
        tags.append("trend_following")
    if "Scalp" in strategy:
        tags.append("quick_trade")
    if date.weekday() == 3:  # Thursday
        tags.append("expiry_day")
    
    return {
        "date": date,
        "time": trade_time,
        "instrument": instrument,
        "trade_type": random.choice(["BUY", "SELL"]),
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "quantity": quantity,
        "pnl": round(pnl, 2),
        "pnl_percent": round(pnl_pct, 2),
        "hold_time_minutes": hold_time,
        "strategy": strategy,
        "tags": tags,
        "notes": None,
        "is_revenge_trade": False,
        "is_overtrade": False,
        "is_tilt_trade": False,
    }


def _generate_revenge_trades(date: datetime, trigger_loss: float) -> list[dict[str, Any]]:
    """Generate revenge trades after a big loss."""
    trades = []
    num_trades = random.randint(3, 5)
    
    for i in range(num_trades):
        trade = _generate_normal_trade(date, session="afternoon")
        
        # Revenge trades have higher loss rate (60-70% losers)
        if random.random() < 0.65:
            # Force a loss
            trade["pnl"] = -abs(trade["pnl"]) * random.uniform(1.2, 2.0)
            trade["pnl_percent"] = -abs(trade["pnl_percent"]) * random.uniform(1.2, 2.0)
            trade["exit_price"] = trade["entry_price"] * (1 + trade["pnl_percent"] / 100)
        
        # Shorter hold times
        trade["hold_time_minutes"] = max(3, trade["hold_time_minutes"] // 2)
        
        # Larger position sizes
        trade["quantity"] = int(trade["quantity"] * random.uniform(1.5, 2.5))
        trade["pnl"] = trade["pnl"] * random.uniform(1.5, 2.5)
        
        trade["is_revenge_trade"] = True
        trade["tags"].append("revenge_trade")
        trade["notes"] = f"Revenge trade after ₹{abs(trigger_loss):,.0f} loss"
        
        trades.append(trade)
    
    return trades


def _generate_overtrade_day(date: datetime) -> list[dict[str, Any]]:
    """Generate an overtrading day with 20+ trades."""
    trades = []
    num_trades = random.randint(20, 30)
    
    for i in range(num_trades):
        # Determine session based on trade number
        if i < 8:
            session = "morning"
        elif i < 16:
            session = "midday"
        else:
            session = "afternoon"
        
        trade = _generate_normal_trade(date, session=session)
        
        # Later trades have worse win rate
        if i > 15 and random.random() < 0.6:
            trade["pnl"] = -abs(trade["pnl"])
            trade["pnl_percent"] = -abs(trade["pnl_percent"])
            trade["exit_price"] = trade["entry_price"] * (1 + trade["pnl_percent"] / 100)
        
        trade["is_overtrade"] = True
        trade["tags"].append("overtrade")
        
        trades.append(trade)
    
    return trades


def _generate_tilt_trades(date: datetime, after_losses: int) -> list[dict[str, Any]]:
    """Generate tilt/emotional trades after consecutive losses."""
    trades = []
    num_trades = random.randint(2, 4)
    
    for i in range(num_trades):
        trade = _generate_normal_trade(date)
        
        # Random entries, no clear setup - higher loss rate
        if random.random() < 0.7:
            trade["pnl"] = -abs(trade["pnl"]) * random.uniform(1.0, 1.5)
            trade["pnl_percent"] = -abs(trade["pnl_percent"]) * random.uniform(1.0, 1.5)
            trade["exit_price"] = trade["entry_price"] * (1 + trade["pnl_percent"] / 100)
        
        # Random strategy (abandoned original)
        trade["strategy"] = random.choice(STRATEGIES)
        
        trade["is_tilt_trade"] = True
        trade["tags"].append("tilt_trade")
        trade["tags"].append("emotional")
        trade["notes"] = f"Emotional trade after {after_losses} consecutive losses"
        
        trades.append(trade)
    
    return trades


def _generate_recovery_trades(date: datetime) -> list[dict[str, Any]]:
    """Generate disciplined recovery trades."""
    trades = []
    num_trades = random.randint(3, 6)
    
    for i in range(num_trades):
        trade = _generate_normal_trade(date, session="morning")
        
        # Higher win rate during recovery
        if random.random() < 0.65:
            trade["pnl"] = abs(trade["pnl"])
            trade["pnl_percent"] = abs(trade["pnl_percent"])
            trade["exit_price"] = trade["entry_price"] * (1 + trade["pnl_percent"] / 100)
        
        # Smaller position sizes
        trade["quantity"] = max(trade["quantity"] // 2, 50)
        trade["pnl"] = trade["pnl"] / 2
        
        trade["tags"].append("recovery")
        trade["tags"].append("disciplined")
        trade["notes"] = "Disciplined trade with reduced size"
        
        trades.append(trade)
    
    return trades


def generate_trade_history(
    user_id: uuid.UUID,
    days: int = 65,
    start_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Generate 60-70 days of realistic trade history with behavioral patterns.
    
    Patterns injected:
    - Revenge Trading Days (5-7 days)
    - Overtrading Days (8-10 days)
    - Tilt/Emotional Days (4-6 days)
    - Loss Streak Periods (3-4 periods)
    - Recovery Days (5-7 days)
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    all_trades = []
    
    # Plan special days
    total_days = days
    
    # Select days for special patterns
    revenge_days = random.sample(range(10, total_days - 5), random.randint(5, 7))
    overtrade_days = random.sample(
        [d for d in range(total_days) if d not in revenge_days],
        random.randint(8, 10)
    )
    tilt_days = random.sample(
        [d for d in range(total_days) if d not in revenge_days and d not in overtrade_days],
        random.randint(4, 6)
    )
    recovery_days = random.sample(
        [d for d in range(total_days) if d not in revenge_days and d not in overtrade_days and d not in tilt_days],
        random.randint(5, 7)
    )
    
    # Track consecutive losses for tilt detection
    consecutive_losses = 0
    last_big_loss = 0
    
    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Skip weekends
        if current_date.weekday() >= 5:
            continue
        
        day_trades = []
        
        if day_offset in overtrade_days:
            # Overtrading day
            day_trades = _generate_overtrade_day(current_date)
        elif day_offset in revenge_days and last_big_loss > 5000:
            # Revenge trading day (after big loss)
            day_trades = _generate_revenge_trades(current_date, last_big_loss)
        elif day_offset in tilt_days and consecutive_losses >= 3:
            # Tilt trading day
            day_trades = _generate_tilt_trades(current_date, consecutive_losses)
        elif day_offset in recovery_days:
            # Recovery day
            day_trades = _generate_recovery_trades(current_date)
        else:
            # Normal trading day
            num_trades = random.randint(5, 15)
            
            # Thursday (expiry) has more trades
            if current_date.weekday() == 3:
                num_trades = random.randint(10, 20)
            
            # Monday is cautious
            if current_date.weekday() == 0:
                num_trades = random.randint(3, 8)
            
            # Friday has fewer trades
            if current_date.weekday() == 4:
                num_trades = random.randint(4, 10)
            
            for _ in range(num_trades):
                day_trades.append(_generate_normal_trade(current_date))
        
        # Track losses for pattern triggers
        for trade in day_trades:
            trade["user_id"] = user_id
            
            if trade["pnl"] < 0:
                consecutive_losses += 1
                if trade["pnl"] < -5000:
                    last_big_loss = abs(trade["pnl"])
            else:
                consecutive_losses = 0
        
        all_trades.extend(day_trades)
    
    return all_trades


class TradeHistoryService:
    """Service for managing trade history and analytics."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def generate_and_save_history(
        self,
        user_id: uuid.UUID,
        days: int = 65,
    ) -> int:
        """Generate and save trade history to database."""
        trades_data = generate_trade_history(user_id, days)
        
        for trade_data in trades_data:
            trade = Trade(
                id=uuid.uuid4(),
                user_id=trade_data["user_id"],
                date=trade_data["date"],
                time=trade_data["time"],
                instrument=trade_data["instrument"],
                trade_type=trade_data["trade_type"],
                entry_price=Decimal(str(trade_data["entry_price"])),
                exit_price=Decimal(str(trade_data["exit_price"])),
                quantity=trade_data["quantity"],
                pnl=Decimal(str(trade_data["pnl"])),
                pnl_percent=Decimal(str(trade_data["pnl_percent"])),
                hold_time_minutes=trade_data["hold_time_minutes"],
                strategy=trade_data["strategy"],
                tags=trade_data["tags"],
                notes=trade_data["notes"],
                is_revenge_trade=trade_data["is_revenge_trade"],
                is_overtrade=trade_data["is_overtrade"],
                is_tilt_trade=trade_data["is_tilt_trade"],
            )
            self._session.add(trade)
        
        await self._session.commit()
        return len(trades_data)
    
    async def get_trades(
        self,
        user_id: uuid.UUID,
        days: int | None = None,
        strategy: str | None = None,
        instrument: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get trade history with optional filters and pagination."""
        from sqlalchemy import func
        
        # Base query for filtering
        base_stmt = select(Trade).where(Trade.user_id == user_id)
        
        if days:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            base_stmt = base_stmt.where(Trade.date >= start_date)
        
        if strategy:
            base_stmt = base_stmt.where(Trade.strategy == strategy)
        
        if instrument:
            base_stmt = base_stmt.where(Trade.instrument.ilike(f"%{instrument}%"))
        
        # Get total count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Apply ordering and pagination
        stmt = base_stmt.order_by(Trade.date.desc(), Trade.time.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self._session.execute(stmt)
        trades = result.scalars().all()
        
        items = [
            {
                "id": str(t.id),
                "date": t.date.isoformat(),
                "time": t.time,
                "instrument": t.instrument,
                "trade_type": t.trade_type,
                "entry_price": float(t.entry_price),
                "exit_price": float(t.exit_price),
                "quantity": t.quantity,
                "pnl": float(t.pnl),
                "pnl_percent": float(t.pnl_percent),
                "hold_time_minutes": t.hold_time_minutes,
                "strategy": t.strategy,
                "tags": t.tags,
                "notes": t.notes,
                "is_revenge_trade": t.is_revenge_trade,
                "is_overtrade": t.is_overtrade,
                "is_tilt_trade": t.is_tilt_trade,
            }
            for t in trades
        ]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total,
        }
    
    async def calculate_analytics(
        self,
        user_id: uuid.UUID,
        days: int | None = None,
    ) -> dict:
        """Calculate comprehensive analytics from trade history."""
        result = await self.get_trades(user_id, days, limit=10000)
        trades = result["items"]
        
        if not trades:
            return self._empty_analytics()
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t["pnl"] for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        max_win = max((t["pnl"] for t in trades), default=0)
        max_loss = min((t["pnl"] for t in trades), default=0)
        
        # Profit factor
        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Consecutive wins/losses
        max_consecutive_wins, max_consecutive_losses = self._calculate_streaks(trades)
        
        # Drawdown
        max_drawdown, max_drawdown_pct = self._calculate_drawdown(trades)
        
        # Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(trades)
        
        # Behavioral stats
        revenge_trades = [t for t in trades if t["is_revenge_trade"]]
        overtrade_trades = [t for t in trades if t["is_overtrade"]]
        tilt_trades = [t for t in trades if t["is_tilt_trade"]]
        
        revenge_trade_loss = sum(t["pnl"] for t in revenge_trades if t["pnl"] < 0)
        tilt_trade_loss = sum(t["pnl"] for t in tilt_trades if t["pnl"] < 0)
        
        # Overtrade days
        overtrade_dates = set(t["date"][:10] for t in overtrade_trades)
        overtrade_impact = sum(t["pnl"] for t in overtrade_trades)
        
        # Time-based stats
        best_hour, worst_hour = self._analyze_hours(trades)
        best_day, worst_day = self._analyze_days(trades)
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(avg_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "max_win": round(max_win, 2),
            "max_loss": round(max_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else 999.99,
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_percent": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "revenge_trade_count": len(revenge_trades),
            "revenge_trade_loss": round(revenge_trade_loss, 2),
            "overtrade_days": len(overtrade_dates),
            "overtrade_impact": round(overtrade_impact, 2),
            "tilt_trade_count": len(tilt_trades),
            "tilt_trade_loss": round(tilt_trade_loss, 2),
            "best_trading_hour": best_hour,
            "worst_trading_hour": worst_hour,
            "best_trading_day": best_day,
            "worst_trading_day": worst_day,
        }
    
    async def get_strategy_performance(self, user_id: uuid.UUID, days: int | None = None) -> list[dict]:
        """Get performance breakdown by strategy."""
        result = await self.get_trades(user_id, days, limit=10000)
        trades = result["items"]
        
        strategy_stats = {}
        for trade in trades:
            strategy = trade["strategy"]
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"trades": [], "wins": 0, "total_pnl": 0}
            
            strategy_stats[strategy]["trades"].append(trade)
            strategy_stats[strategy]["total_pnl"] += trade["pnl"]
            if trade["pnl"] > 0:
                strategy_stats[strategy]["wins"] += 1
        
        result = []
        for strategy, stats in strategy_stats.items():
            num_trades = len(stats["trades"])
            result.append({
                "strategy": strategy,
                "trades": num_trades,
                "win_rate": round(stats["wins"] / num_trades * 100, 2) if num_trades > 0 else 0,
                "avg_pnl": round(stats["total_pnl"] / num_trades, 2) if num_trades > 0 else 0,
                "total_pnl": round(stats["total_pnl"], 2),
            })
        
        return sorted(result, key=lambda x: x["total_pnl"], reverse=True)
    
    async def get_weekly_pnl(self, user_id: uuid.UUID, weeks: int = 10) -> list[dict]:
        """Get weekly P&L trends."""
        result = await self.get_trades(user_id, days=weeks * 7, limit=10000)
        trades = result["items"]
        
        # Group by week
        weekly_data = {}
        for trade in trades:
            trade_date = datetime.fromisoformat(trade["date"].replace("Z", "+00:00"))
            week_start = trade_date - timedelta(days=trade_date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {"pnl": 0, "trades": 0, "wins": 0}
            
            weekly_data[week_key]["pnl"] += trade["pnl"]
            weekly_data[week_key]["trades"] += 1
            if trade["pnl"] > 0:
                weekly_data[week_key]["wins"] += 1
        
        result = []
        for week_start, data in sorted(weekly_data.items()):
            week_end = (datetime.fromisoformat(week_start) + timedelta(days=6)).strftime("%Y-%m-%d")
            result.append({
                "week_start": week_start,
                "week_end": week_end,
                "pnl": round(data["pnl"], 2),
                "trades": data["trades"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 2) if data["trades"] > 0 else 0,
            })
        
        return result
    
    async def detect_revenge_trade(self, user_id: uuid.UUID, lookback_trades: int = 10) -> dict | None:
        """Detect if recent trades show revenge trading pattern."""
        result = await self.get_trades(user_id, limit=lookback_trades)
        recent_trades = result["items"]
        
        if len(recent_trades) < 3:
            return None
        
        # Check for big loss followed by quick trades
        for i, trade in enumerate(recent_trades[:-2]):
            if trade["pnl"] < -5000:  # Big loss
                subsequent = recent_trades[i+1:i+4]
                if len(subsequent) >= 2:
                    avg_hold = sum(t["hold_time_minutes"] for t in subsequent) / len(subsequent)
                    loss_rate = sum(1 for t in subsequent if t["pnl"] < 0) / len(subsequent)
                    
                    if avg_hold < 15 and loss_rate > 0.5:
                        return {
                            "detected": True,
                            "trigger_loss": trade["pnl"],
                            "subsequent_trades": len(subsequent),
                            "subsequent_loss_rate": round(loss_rate * 100, 2),
                            "message": f"Possible revenge trading detected after ₹{abs(trade['pnl']):,.0f} loss",
                        }
        
        return {"detected": False}
    
    async def detect_overtrading(self, user_id: uuid.UUID, threshold: int = 20) -> dict:
        """Detect overtrading days and their impact."""
        result = await self.get_trades(user_id, limit=10000)
        trades = result["items"]
        
        # Group by date
        daily_trades = {}
        for trade in trades:
            date = trade["date"][:10]
            if date not in daily_trades:
                daily_trades[date] = []
            daily_trades[date].append(trade)
        
        overtrade_days = []
        for date, day_trades in daily_trades.items():
            if len(day_trades) >= threshold:
                total_pnl = sum(t["pnl"] for t in day_trades)
                overtrade_days.append({
                    "date": date,
                    "trade_count": len(day_trades),
                    "pnl": round(total_pnl, 2),
                })
        
        total_impact = sum(d["pnl"] for d in overtrade_days)
        
        return {
            "overtrade_days": overtrade_days,
            "total_days": len(overtrade_days),
            "total_impact": round(total_impact, 2),
            "avg_trades_per_overtrade_day": round(
                sum(d["trade_count"] for d in overtrade_days) / len(overtrade_days), 1
            ) if overtrade_days else 0,
        }
    
    async def get_trade_summary_for_ai(self, user_id: uuid.UUID) -> dict:
        """Get summary data formatted for AI system prompt."""
        analytics = await self.calculate_analytics(user_id)
        strategy_perf = await self.get_strategy_performance(user_id)
        weekly_pnl = await self.get_weekly_pnl(user_id)
        revenge_alert = await self.detect_revenge_trade(user_id)
        overtrade_info = await self.detect_overtrading(user_id)
        
        return {
            "overall_stats": analytics,
            "strategy_performance": strategy_perf,
            "weekly_pnl": weekly_pnl,
            "recent_patterns": {
                "revenge_trading": revenge_alert,
                "overtrading": overtrade_info,
            },
            "risk_metrics": {
                "max_drawdown": analytics["max_drawdown"],
                "max_drawdown_percent": analytics["max_drawdown_percent"],
                "max_consecutive_losses": analytics["max_consecutive_losses"],
                "sharpe_ratio": analytics["sharpe_ratio"],
            },
        }
    
    def _empty_analytics(self) -> dict:
        """Return empty analytics structure."""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "max_win": 0,
            "max_loss": 0,
            "profit_factor": 0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "max_drawdown": 0,
            "max_drawdown_percent": 0,
            "sharpe_ratio": 0,
            "revenge_trade_count": 0,
            "revenge_trade_loss": 0,
            "overtrade_days": 0,
            "overtrade_impact": 0,
            "tilt_trade_count": 0,
            "tilt_trade_loss": 0,
            "best_trading_hour": "N/A",
            "worst_trading_hour": "N/A",
            "best_trading_day": "N/A",
            "worst_trading_day": "N/A",
        }
    
    def _calculate_streaks(self, trades: list[dict]) -> tuple[int, int]:
        """Calculate max consecutive wins and losses."""
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in reversed(trades):  # Chronological order
            if trade["pnl"] > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def _calculate_drawdown(self, trades: list[dict]) -> tuple[float, float]:
        """Calculate maximum drawdown."""
        if not trades:
            return 0, 0
        
        cumulative = 0
        peak = 0
        max_dd = 0
        max_dd_pct = 0
        
        for trade in reversed(trades):  # Chronological order
            cumulative += trade["pnl"]
            if cumulative > peak:
                peak = cumulative
            
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = (dd / peak * 100) if peak > 0 else 0
        
        return max_dd, max_dd_pct
    
    def _calculate_sharpe_ratio(self, trades: list[dict]) -> float:
        """Calculate simplified Sharpe ratio."""
        if len(trades) < 2:
            return 0
        
        returns = [t["pnl_percent"] for t in trades]
        avg_return = sum(returns) / len(returns)
        
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
        
        # Annualized (assuming ~250 trading days)
        sharpe = (avg_return / std_dev) * (250 ** 0.5)
        return sharpe
    
    def _analyze_hours(self, trades: list[dict]) -> tuple[str, str]:
        """Analyze best and worst trading hours."""
        hour_pnl = {}
        
        for trade in trades:
            hour = trade["time"][:2]
            if hour not in hour_pnl:
                hour_pnl[hour] = 0
            hour_pnl[hour] += trade["pnl"]
        
        if not hour_pnl:
            return "N/A", "N/A"
        
        best_hour = max(hour_pnl, key=hour_pnl.get)
        worst_hour = min(hour_pnl, key=hour_pnl.get)
        
        return f"{best_hour}:00", f"{worst_hour}:00"
    
    def _analyze_days(self, trades: list[dict]) -> tuple[str, str]:
        """Analyze best and worst trading days."""
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        day_pnl = {d: 0 for d in day_names}
        
        for trade in trades:
            trade_date = datetime.fromisoformat(trade["date"].replace("Z", "+00:00"))
            day_name = day_names[trade_date.weekday()]
            day_pnl[day_name] += trade["pnl"]
        
        best_day = max(day_pnl, key=day_pnl.get)
        worst_day = min(day_pnl, key=day_pnl.get)
        
        return best_day, worst_day
