from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.order import Transaction
from app.models.portfolio import Holding, PortfolioConfig
from app.utils.formatters import format_inr

logger = logging.getLogger(__name__)


class AlertDetectorService:
    def __init__(
        self,
        session: AsyncSession,
        analytics_service: Any,
    ) -> None:
        self._session = session
        self._analytics = analytics_service

    # -- Individual detectors --

    async def detect_revenge_trade(
        self, user_id: uuid.UUID, loss_threshold: float = 10000,
    ) -> dict | None:
        """Detect rapid trades after a significant loss (3+ trades within 30 min)."""
        classified = await self._analytics.classify_trades(user_id)
        if len(classified) < 4:
            return None

        for i in range(len(classified) - 3):
            t = classified[i]
            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])

            if trade_pnl < -loss_threshold:
                trigger_time = datetime.fromisoformat(t["created_at"])
                next_trades = classified[i + 1: i + 5]

                if len(next_trades) >= 3:
                    last_time = datetime.fromisoformat(next_trades[-1]["created_at"])
                    window_mins = abs((last_time - trigger_time).total_seconds() / 60)

                    if 0 < window_mins <= 30:
                        revenge_pnl = sum(
                            (float(nt["price"]) - nt["avg_buy_price"]) * float(nt["quantity"])
                            for nt in next_trades
                        )
                        avg_revenge_pnl = revenge_pnl / len(next_trades)

                        if avg_revenge_pnl >= 0:
                            advice = "Even profitable revenge trades carry elevated risk. Consider taking a 15-minute break after significant losses."
                        else:
                            advice = "Consider taking a 15-minute break after significant losses."

                        return {
                            "type": "REVENGE_TRADING",
                            "severity": "high",
                            "title": "Revenge Trading Detected",
                            "description": (
                                f"You placed {len(next_trades)} trades in {round(window_mins)} minutes "
                                f"after losing {format_inr(abs(trade_pnl))} on {t['symbol']}."
                            ),
                            "context": {
                                "trades_placed": len(next_trades),
                                "time_window": round(window_mins),
                                "trigger_loss": abs(trade_pnl),
                                "trigger_trade": t["symbol"],
                                "revenge_trade_pnl": round(revenge_pnl, 2),
                                "avg_revenge_pnl": round(avg_revenge_pnl, 2),
                            },
                            "suggestion": (
                                f"Your average P&L on trades in this pattern is "
                                f"{format_inr(avg_revenge_pnl, show_sign=True)} each. "
                                f"{advice}"
                            ),
                        }
        return None

    async def detect_overtrading(self, user_id: uuid.UUID) -> dict | None:
        """Trigger if today's trade count > 1.3x 7-day average."""
        now = datetime.now(timezone.utc)
        session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = session_start - timedelta(days=7)

        all_trades = await self._analytics.filter_trades(
            user_id, date_range=(week_start, now)
        )
        today_trades = [
            t for t in all_trades
            if datetime.fromisoformat(t["created_at"]) >= session_start
        ]
        past_trades = [
            t for t in all_trades
            if datetime.fromisoformat(t["created_at"]) < session_start
        ]

        # Group past trades by day
        days_seen: set[str] = set()
        for t in past_trades:
            days_seen.add(datetime.fromisoformat(t["created_at"]).date().isoformat())

        num_days = max(len(days_seen), 1)
        avg_count = len(past_trades) / num_days
        today_count = len(today_trades)

        if avg_count == 0:
            return None

        ratio = today_count / avg_count
        if ratio <= 1.3:
            return None

        severity = "high" if ratio > 2 else ("medium" if ratio > 1.5 else "low")
        win_rate_drop = round((ratio - 1) * 18)

        return {
            "type": "OVERTRADING",
            "severity": severity,
            "title": "Elevated Trading Velocity",
            "description": f"You have placed {today_count} trades today. Your 7-day average is {round(avg_count)}.",
            "context": {
                "today_count": today_count,
                "avg_count": round(avg_count),
                "ratio": round(ratio, 1),
                "win_rate_drop": win_rate_drop,
            },
            "suggestion": f"Historically, your win rate drops {win_rate_drop}% on high-volume days. Consider slowing down.",
        }

    async def detect_drawdown(self, user_id: uuid.UUID) -> dict | None:
        """Trigger at >60% of daily loss limit consumed."""
        config_result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = config_result.scalar_one_or_none()
        if config is None:
            return None

        daily_limit = float(config.daily_loss_limit)
        if daily_limit <= 0:
            return None

        # Compute today's realized P&L
        now = datetime.now(timezone.utc)
        session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        classified = await self._analytics.classify_trades(user_id)
        today_trades = [
            t for t in classified
            if datetime.fromisoformat(t["created_at"]) >= session_start
        ]

        if not today_trades:
            return None

        # Running P&L and max drawdown
        running_pnl = 0.0
        max_pnl = 0.0
        max_drawdown = 0.0
        for t in today_trades:
            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            running_pnl += trade_pnl
            if running_pnl > max_pnl:
                max_pnl = running_pnl
            drawdown = max_pnl - running_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        percent_used = (max_drawdown / daily_limit) * 100
        if percent_used <= 60:
            return None

        severity = "critical" if percent_used > 90 else ("high" if percent_used > 75 else "medium")
        buffer = daily_limit - max_drawdown

        return {
            "type": "DRAWDOWN_WARNING",
            "severity": severity,
            "title": "Approaching Daily Loss Limit",
            "description": (
                f"Your max drawdown today is {format_inr(max_drawdown)} "
                f"({round(percent_used)}% of your {format_inr(daily_limit)} limit)."
            ),
            "context": {
                "max_drawdown": round(max_drawdown, 2),
                "daily_loss_limit": daily_limit,
                "percent_used": round(percent_used),
                "buffer": round(buffer, 2),
                "current_pnl": round(running_pnl, 2),
            },
            "suggestion": f"You have {format_inr(buffer)} buffer remaining. Consider reducing position sizes or stopping for the day.",
        }

    async def detect_concentration(self, user_id: uuid.UUID) -> dict | None:
        """Trigger when single instrument >50% of total invested value."""
        exposure = await self._analytics.calculate_exposure(user_id)
        if not exposure:
            return None

        max_pos = max(exposure, key=lambda e: e["allocation_pct"])
        if max_pos["allocation_pct"] <= 50:
            return None

        return {
            "type": "CONCENTRATION_RISK",
            "severity": "high" if max_pos["allocation_pct"] > 70 else "medium",
            "title": "High Concentration Risk",
            "description": (
                f"{round(max_pos['allocation_pct'])}% of your portfolio "
                f"({format_inr(max_pos['value'])}) is in {max_pos['group']}."
            ),
            "context": {
                "symbol": max_pos["group"],
                "value": max_pos["value"],
                "percent": round(max_pos["allocation_pct"]),
            },
            "suggestion": "Consider diversifying across instruments to reduce single-stock risk.",
        }

    async def detect_time_risk(self, user_id: uuid.UUID) -> dict | None:
        """Trigger when afternoon (>=1 PM) win rate <40% AND 15+ points below morning rate."""
        now = datetime.now(timezone.utc)
        if now.hour < 13:
            return None

        win_rates = await self._analytics.get_win_rate_by_time(user_id)
        morning = win_rates.get("morning", {})
        afternoon = win_rates.get("afternoon", {})

        morning_wr = morning.get("win_rate", 0)
        afternoon_wr = afternoon.get("win_rate", 0)

        if afternoon_wr >= 40 or (morning_wr - afternoon_wr) <= 15:
            return None

        difference = round(morning_wr - afternoon_wr)
        afternoon_pnl = afternoon.get("pnl", 0)

        return {
            "type": "TIME_RISK",
            "severity": "medium",
            "title": "Low Win Rate Time Period",
            "description": (
                f"Your win rate after 1 PM is {round(afternoon_wr)}% vs "
                f"{round(morning_wr)}% in the morning ({difference}pp difference)."
            ),
            "context": {
                "current_hour": now.hour,
                "afternoon_win_rate": round(afternoon_wr),
                "morning_win_rate": round(morning_wr),
                "difference": difference,
                "afternoon_pnl": round(afternoon_pnl, 2),
                "afternoon_trades": afternoon.get("trades", 0),
            },
            "suggestion": (
                f"Your afternoon trades have cost you {format_inr(abs(afternoon_pnl))} this month. "
                f"Consider reducing trade frequency during afternoon hours."
            ),
        }

    async def detect_loss_streak(self, user_id: uuid.UUID) -> dict | None:
        """Detect 3+ consecutive losses."""
        classified = await self._analytics.classify_trades(user_id)
        if len(classified) < 3:
            return None

        # classified is chronological; check from most recent
        streak = 0
        total_loss = 0.0
        streak_trades = []

        for t in reversed(classified):
            if not t["is_win"]:
                streak += 1
                loss = abs((float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"]))
                total_loss += loss
                streak_trades.append({"symbol": t["symbol"], "pnl": -loss})
            else:
                break

        if streak < 3:
            return None

        return {
            "type": "LOSS_STREAK",
            "severity": "high" if streak >= 5 else "medium",
            "title": f"{streak} Consecutive Losses",
            "description": f"Your last {streak} trades have all been losses, totaling {format_inr(total_loss)}.",
            "context": {
                "streak": streak,
                "total_loss": round(total_loss, 2),
                "trades": streak_trades[:5],
            },
            "suggestion": "Consider taking a break to reset mentally. Loss streaks often lead to revenge trading.",
        }

    async def detect_position_escalation(self, user_id: uuid.UUID) -> dict | None:
        """Detect position size increase >30% after a loss (martingale pattern)."""
        classified = await self._analytics.classify_trades(user_id)
        if len(classified) < 4:
            return None

        # Most recent trades first
        recent = list(reversed(classified))[-4:]

        for i in range(1, len(recent)):
            current = recent[i]
            previous = recent[i - 1]

            prev_qty = float(previous["quantity"])
            curr_qty = float(current["quantity"])

            if not previous["is_win"] and prev_qty > 0 and curr_qty > prev_qty * 1.3:
                size_increase = round(((curr_qty / prev_qty) - 1) * 100)
                return {
                    "type": "POSITION_ESCALATION",
                    "severity": "high",
                    "title": "Position Size Escalation Detected",
                    "description": (
                        f"You increased position size by {size_increase}% after a losing trade. "
                        f"This martingale-like behavior is risky."
                    ),
                    "context": {
                        "size_increase": size_increase,
                        "recent_trades": [
                            {
                                "symbol": t["symbol"],
                                "quantity": float(t["quantity"]),
                                "is_win": t["is_win"],
                            }
                            for t in recent
                        ],
                    },
                    "suggestion": "Increasing position size after losses amplifies risk. Consider keeping position sizes consistent.",
                }

        return None

    # -- Orchestrator --

    async def evaluate_all(self, user_id: uuid.UUID) -> list[dict]:
        """Run all detectors, persist new alerts, return active alerts."""
        # Dedup: fetch existing undismissed alert types for this user
        existing_result = await self._session.execute(
            select(Alert.type).where(
                Alert.user_id == user_id,
                Alert.dismissed == False,  # noqa: E712
            )
        )
        existing_types: set[str] = {row[0] for row in existing_result.all()}

        detectors = [
            self.detect_revenge_trade,
            self.detect_overtrading,
            self.detect_drawdown,
            self.detect_concentration,
            self.detect_time_risk,
            self.detect_loss_streak,
            self.detect_position_escalation,
        ]

        new_alerts = []
        for detector in detectors:
            try:
                result = await detector(user_id)
                if result is not None and result["type"] not in existing_types:
                    alert = Alert(
                        user_id=user_id,
                        type=result["type"],
                        severity=result["severity"],
                        title=result["title"],
                        description=result["description"],
                        context=result.get("context", {}),
                        suggestion=result.get("suggestion", ""),
                    )
                    self._session.add(alert)
                    new_alerts.append(result)
                    existing_types.add(result["type"])
            except Exception:
                logger.exception(f"Alert detector failed: {detector.__name__}")

        if new_alerts:
            await self._session.commit()

        return new_alerts

    # -- Risk metrics --

    async def calculate_risk_metrics(self, user_id: uuid.UUID) -> dict:
        """Return: drawdown %, trade velocity, concentration %, today's win rate, largest loss."""
        now = datetime.now(timezone.utc)
        session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        classified = await self._analytics.classify_trades(user_id)
        today_trades = [
            t for t in classified
            if datetime.fromisoformat(t["created_at"]) >= session_start
        ]

        # Drawdown (today only)
        running_pnl = 0.0
        max_pnl = 0.0
        max_drawdown = 0.0
        for t in today_trades:
            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            running_pnl += trade_pnl
            if running_pnl > max_pnl:
                max_pnl = running_pnl
            drawdown = max_pnl - running_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Drawdown (overall — across all classified trades)
        overall_running = 0.0
        overall_peak = 0.0
        overall_max_dd = 0.0
        for t in classified:
            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            overall_running += trade_pnl
            if overall_running > overall_peak:
                overall_peak = overall_running
            dd = overall_peak - overall_running
            if dd > overall_max_dd:
                overall_max_dd = dd
        config_result = await self._session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = config_result.scalar_one_or_none()
        daily_limit = float(config.daily_loss_limit) if config else 25000
        initial_cash = float(config.initial_cash) if config else 0
        overall_dd_pct = (overall_max_dd / initial_cash * 100) if initial_cash > 0 else 0

        # Trade velocity
        week_start = session_start - timedelta(days=7)
        all_trades = await self._analytics.filter_trades(
            user_id, date_range=(week_start, now)
        )
        past_trades = [
            t for t in all_trades
            if datetime.fromisoformat(t["created_at"]) < session_start
        ]
        days_seen: set[str] = set()
        for t in past_trades:
            days_seen.add(datetime.fromisoformat(t["created_at"]).date().isoformat())
        avg_per_day = len(past_trades) / max(len(days_seen), 1)
        trade_velocity = (len(today_trades) / avg_per_day * 100) if avg_per_day > 0 else 0

        # Concentration
        exposure = await self._analytics.calculate_exposure(user_id)
        max_concentration = max((e["allocation_pct"] for e in exposure), default=0)

        # Margin utilization - use initial_cash as the total available margin
        holdings_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id)
        )
        holdings = holdings_result.scalars().all()
        invested_value = sum(float(h.avg_price) * float(h.quantity) for h in holdings)

        # Use initial_cash as the total margin available
        margin_total = initial_cash if initial_cash > 0 else 1  # Avoid division by zero
        # Calculate margin utilization as percentage of initial capital
        margin_utilization_pct = (invested_value / margin_total * 100) if margin_total > 0 else 0

        # Win rate
        today_wins = sum(1 for t in today_trades if t["is_win"])
        today_win_rate = (today_wins / len(today_trades) * 100) if today_trades else 0

        # Largest loss
        largest_loss_amount = 0.0
        largest_loss_symbol = "None"
        for t in today_trades:
            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            if trade_pnl < -largest_loss_amount:
                largest_loss_amount = abs(trade_pnl)
                largest_loss_symbol = t["symbol"]

        return {
            "drawdown": {
                "current": round(max_drawdown, 2),
                "percent": round((max_drawdown / daily_limit) * 100, 1) if daily_limit > 0 else 0,
            },
            "overall_drawdown": {
                "current": round(overall_max_dd, 2),
                "percent": round(overall_dd_pct, 1),
            },
            "daily_loss_limit": daily_limit,
            "trade_velocity": {
                "count": len(today_trades),
                "percent": round(trade_velocity, 1),
                "avg_per_day": round(avg_per_day),
            },
            "concentration": {
                "percent": round(max_concentration, 1),
            },
            "margin": {
                "used": round(invested_value, 2),
                "total": round(margin_total, 2),
                "utilization_pct": round(margin_utilization_pct, 1),
            },
            "today_stats": {
                "trades": len(today_trades),
                "win_rate": round(today_win_rate, 1),
                "pnl": round(running_pnl, 2),
                "largest_loss": {
                    "amount": round(largest_loss_amount, 2),
                    "instrument": largest_loss_symbol,
                },
            },
        }
