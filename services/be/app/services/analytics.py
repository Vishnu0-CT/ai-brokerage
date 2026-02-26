from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Transaction
from app.models.portfolio import Holding

# Indian stock/index correlations only
BETA_TABLE: dict[str, dict[str, float]] = {
    "NIFTY": {"RELIANCE": 0.85, "INFY": 0.75, "TCS": 0.70, "BANKNIFTY": 0.95},
    "BANKNIFTY": {"NIFTY": 0.95, "RELIANCE": 0.80, "INFY": 0.70, "TCS": 0.65},
    "RELIANCE": {"NIFTY": 0.85, "INFY": 0.40, "TCS": 0.35},
    "INFY": {"NIFTY": 0.75, "TCS": 0.80, "RELIANCE": 0.40},
    "TCS": {"NIFTY": 0.70, "INFY": 0.80, "RELIANCE": 0.35},
}


class AnalyticsService:
    def __init__(self, session: AsyncSession, price_service: Any) -> None:
        self._session = session
        self._price_service = price_service

    # -- filter_trades --

    async def filter_trades(
        self,
        user_id: uuid.UUID,
        instrument: str | None = None,
        date_range: tuple[datetime, datetime] | None = None,
        direction: str | None = None,
        trade_type: str | None = None,
    ) -> list[dict]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if instrument:
            stmt = stmt.where(Transaction.symbol == instrument)
        if direction:
            stmt = stmt.where(Transaction.side == direction)
        if date_range:
            stmt = stmt.where(
                Transaction.created_at >= date_range[0],
                Transaction.created_at <= date_range[1],
            )

        stmt = stmt.order_by(Transaction.created_at.desc())
        result = await self._session.execute(stmt)

        return [
            {
                "symbol": t.symbol,
                "side": t.side,
                "quantity": t.quantity,
                "price": t.price,
                "total": t.quantity * t.price,
                "created_at": t.created_at.isoformat(),
            }
            for t in result.scalars().all()
        ]

    # -- aggregate_metrics --

    async def aggregate_metrics(
        self,
        user_id: uuid.UUID,
        group_by: str | None = None,
        metric: str = "pnl",
        filter_params: dict | None = None,
    ) -> list[dict]:
        trades = await self.filter_trades(user_id, **(filter_params or {}))

        dispatch = {
            "count": self._aggregate_count,
            "pnl": self._aggregate_pnl,
            "total_volume": self._aggregate_volume,
            "win_rate": self._aggregate_win_rate,
            "avg_return": self._aggregate_avg_return,
        }
        fn = dispatch.get(metric)
        if fn is None:
            raise ValueError(f"Unknown metric: {metric}")
        return fn(trades, group_by)

    # -- calculate_exposure --

    async def calculate_exposure(
        self, user_id: uuid.UUID, by: str = "instrument",
    ) -> list[dict]:
        result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id)
        )
        holdings = result.scalars().all()

        enriched = []
        for h in holdings:
            tick = await self._price_service.get_price(h.symbol) if self._price_service else None
            current_price = tick.price if tick else float(h.avg_price)
            value = current_price * float(h.quantity)
            enriched.append({
                "symbol": h.symbol,
                "side": h.side,
                "value": value,
                "quantity": float(h.quantity),
            })

        total = sum(e["value"] for e in enriched)

        return [
            {
                "group": e["symbol"],
                "side": e["side"],
                "value": round(e["value"], 2),
                "allocation_pct": round(e["value"] / total * 100, 2) if total > 0 else 0,
            }
            for e in enriched
        ]

    # -- simulate_scenario (cross-asset correlation) --

    async def simulate_scenario(
        self,
        user_id: uuid.UUID,
        symbol: str | None = None,
        price_change: float | None = None,
        price_change_points: float | None = None,
        iv_change: float | None = None,
        time_decay_days: float | None = None,
        correlations: bool = True,
    ) -> dict:
        stmt = select(Holding).where(Holding.user_id == user_id)
        if symbol and not correlations:
            stmt = stmt.where(Holding.symbol == symbol)
        result = await self._session.execute(stmt)
        holdings = result.scalars().all()

        corr_betas = BETA_TABLE.get(symbol, {}) if (symbol and correlations) else {}

        target_price: float | None = None
        if symbol and price_change_points is not None and corr_betas:
            tick = await self._price_service.get_price(symbol) if self._price_service else None
            target_price = tick.price if tick else None

        per_position = []
        total_impact = 0.0

        for h in holdings:
            tick = await self._price_service.get_price(h.symbol) if self._price_service else None
            current_price = tick.price if tick else float(h.avg_price)
            qty = float(h.quantity)
            side = h.side
            impact = 0.0
            beta: float | None = None
            is_correlated = False

            if symbol and h.symbol == symbol:
                if price_change_points is not None:
                    impact = qty * price_change_points
                elif price_change is not None:
                    impact = qty * current_price * price_change
                if side == "short":
                    impact = -impact
            elif symbol and h.symbol in corr_betas:
                beta = corr_betas[h.symbol]
                is_correlated = True
                if price_change is not None:
                    impact = qty * current_price * price_change * beta
                elif price_change_points is not None and target_price:
                    pct_change = price_change_points / target_price
                    impact = qty * current_price * pct_change * beta
                if side == "short":
                    impact = -impact
            elif not symbol:
                if price_change_points is not None:
                    impact = qty * price_change_points
                elif price_change is not None:
                    impact = qty * current_price * price_change
                if side == "short":
                    impact = -impact
            else:
                continue

            if h.symbol == symbol and price_change_points is not None:
                scenario_price = current_price + price_change_points
            elif h.symbol == symbol and price_change is not None:
                scenario_price = current_price * (1 + price_change)
            elif is_correlated and price_change is not None:
                scenario_price = current_price * (1 + price_change * beta)
            elif is_correlated and price_change_points is not None and target_price:
                pct_change = price_change_points / target_price
                scenario_price = current_price * (1 + pct_change * beta)
            elif not symbol:
                if price_change_points is not None:
                    scenario_price = current_price + price_change_points
                else:
                    scenario_price = current_price * (1 + (price_change or 0))
            else:
                scenario_price = current_price

            entry = {
                "symbol": h.symbol,
                "side": side,
                "quantity": qty,
                "current_price": current_price,
                "scenario_price": round(scenario_price, 2),
                "pnl_impact": round(impact, 2),
            }
            if is_correlated:
                entry["beta"] = beta
                entry["correlated_to"] = symbol
            per_position.append(entry)
            total_impact += impact

        return {
            "per_position": per_position,
            "total_pnl_impact": round(total_impact, 2),
            "assumptions": {
                "symbol": symbol,
                "price_change": price_change,
                "price_change_points": price_change_points,
                "iv_change": iv_change,
                "time_decay_days": time_decay_days,
                "correlations": correlations,
            },
        }

    # -- classify_trades (win/loss per sell) --

    async def classify_trades(self, user_id: uuid.UUID) -> list[dict]:
        trades = await self.filter_trades(user_id)
        trades.reverse()  # chronological

        buy_tracker: dict[str, dict[str, float]] = {}
        classified: list[dict] = []

        for t in trades:
            symbol = t["symbol"]
            if t["side"] == "buy":
                bt = buy_tracker.setdefault(symbol, {"total_cost": 0.0, "total_qty": 0.0})
                bt["total_cost"] += float(t["total"])
                bt["total_qty"] += float(t["quantity"])
            elif t["side"] == "sell":
                bt = buy_tracker.get(symbol, {"total_cost": 0.0, "total_qty": 0.0})
                avg_buy = bt["total_cost"] / bt["total_qty"] if bt["total_qty"] > 0 else 0
                sell_price = float(t["price"])
                is_win = sell_price > avg_buy

                qty = float(t["quantity"])
                loss_amount = abs((sell_price - avg_buy) * qty) if not is_win else 0.0

                classified.append({
                    **t,
                    "avg_buy_price": round(avg_buy, 2),
                    "is_win": is_win,
                    "return_pct": round((sell_price - avg_buy) / avg_buy * 100, 2) if avg_buy > 0 else 0,
                    "loss_amount": round(loss_amount, 2),
                })

        return classified

    # -- analyze_post_event_trades --

    async def analyze_post_event_trades(
        self,
        user_id: uuid.UUID,
        event_type: str = "after_loss",
        lookback_count: int = 50,
        min_loss_amount: float | None = None,
    ) -> dict:
        classified = await self.classify_trades(user_id)
        if not classified:
            return {"trades_analyzed": 0, "pattern": event_type, "stats": {}}

        classified = classified[-lookback_count:]

        def _is_qualifying_loss(trade: dict) -> bool:
            if trade["is_win"]:
                return False
            if min_loss_amount is not None:
                return trade.get("loss_amount", 0) >= min_loss_amount
            return True

        if event_type == "after_loss":
            post_event = [
                classified[i] for i in range(1, len(classified))
                if _is_qualifying_loss(classified[i - 1])
            ]
        elif event_type == "after_win":
            post_event = [
                classified[i] for i in range(1, len(classified))
                if classified[i - 1]["is_win"]
            ]
        elif event_type == "during_streak":
            post_event = []
            consecutive_losses = 0
            for t in classified:
                if _is_qualifying_loss(t):
                    consecutive_losses += 1
                else:
                    consecutive_losses = 0
                if consecutive_losses >= 2:
                    post_event.append(t)
        else:
            return {"error": f"Unknown event_type: {event_type}"}

        if not post_event:
            return {
                "trades_analyzed": len(classified),
                "pattern": event_type,
                "matching_trades": 0,
                "stats": {"win_rate": 0, "avg_return_pct": 0, "avg_subsequent_loss": 0, "sample_size": 0},
            }

        wins = sum(1 for t in post_event if t["is_win"])
        avg_return = sum(t["return_pct"] for t in post_event) / len(post_event)
        losses_in_post = [t for t in post_event if not t["is_win"]]
        avg_subsequent_loss = (
            sum(t.get("loss_amount", 0) for t in losses_in_post) / len(losses_in_post)
            if losses_in_post else 0.0
        )

        return {
            "trades_analyzed": len(classified),
            "pattern": event_type,
            "matching_trades": len(post_event),
            "stats": {
                "win_rate": round(wins / len(post_event) * 100, 2),
                "avg_return_pct": round(avg_return, 2),
                "avg_subsequent_loss": round(avg_subsequent_loss, 2),
                "sample_size": len(post_event),
            },
        }

    # -- compute_trading_readiness --

    async def compute_trading_readiness(self, user_id: uuid.UUID) -> dict:
        classified = await self.classify_trades(user_id)

        streak = 0
        for t in reversed(classified):
            if not t["is_win"]:
                streak += 1
            else:
                break

        now = datetime.now(timezone.utc)
        current_hour = now.hour
        hour_trades = [
            t for t in classified
            if datetime.fromisoformat(t["created_at"]).hour == current_hour
        ]
        if hour_trades:
            hour_win_rate = sum(1 for t in hour_trades if t["is_win"]) / len(hour_trades) * 100
        else:
            hour_win_rate = 50.0

        session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = [
            t for t in classified
            if datetime.fromisoformat(t["created_at"]) >= session_start
        ]
        session_pnl = sum(
            (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            for t in today_trades
        )

        caution_factors = 0
        favorable_factors = 0

        if streak >= 3:
            caution_factors += 2
        elif streak >= 2:
            caution_factors += 1

        if hour_win_rate < 40:
            caution_factors += 1
        elif hour_win_rate > 60:
            favorable_factors += 1

        if session_pnl < -1000:
            caution_factors += 1
        elif session_pnl > 1000:
            favorable_factors += 1

        if caution_factors >= 2:
            signal = "caution"
        elif favorable_factors >= 2:
            signal = "favorable"
        else:
            signal = "neutral"

        return {
            "signal": signal,
            "factors": {
                "recent_loss_streak": streak,
                "hour_win_rate": round(hour_win_rate, 1),
                "session_pnl": round(session_pnl, 2),
                "current_hour_utc": current_hour,
                "trades_this_hour": len(hour_trades),
            },
        }

    # -- compute_behavioral_context --

    async def compute_behavioral_context(self, user_id: uuid.UUID) -> dict | None:
        try:
            readiness = await self.compute_trading_readiness(user_id)
        except Exception:
            readiness = None

        try:
            exposure = await self.calculate_exposure(user_id)
            top_position = max(exposure, key=lambda e: e["allocation_pct"]) if exposure else None
        except Exception:
            top_position = None

        if readiness is None and top_position is None:
            return None

        return {
            "trading_readiness": readiness,
            "top_concentration": top_position,
        }

    # -- period filtering --

    def _period_to_cutoff(self, period: str) -> datetime:
        now = datetime.now(timezone.utc)
        mapping = {
            "7d": timedelta(days=7),
            "14d": timedelta(days=14),
            "1m": timedelta(days=30),
            "30d": timedelta(days=30),
            "3m": timedelta(days=90),
        }
        delta = mapping.get(period, timedelta(days=30))
        return now - delta

    def _filter_by_period(self, classified: list[dict], period: str) -> list[dict]:
        cutoff = self._period_to_cutoff(period)
        return [
            t for t in classified
            if datetime.fromisoformat(t["created_at"]) >= cutoff
        ]

    # -- Enhanced analytics from tradeai --

    async def get_win_rate_by_time(self, user_id: uuid.UUID, period: str = "1m") -> dict:
        """Win rate for morning (9:15-10:30), midday (10:30-13:00), afternoon (13:00-15:30)."""
        classified = await self.classify_trades(user_id)
        classified = self._filter_by_period(classified, period)

        buckets = {
            "morning": {"trades": 0, "wins": 0, "pnl": 0.0},
            "midday": {"trades": 0, "wins": 0, "pnl": 0.0},
            "afternoon": {"trades": 0, "wins": 0, "pnl": 0.0},
        }

        for t in classified:
            dt = datetime.fromisoformat(t["created_at"])
            hour, minute = dt.hour, dt.minute
            total_mins = hour * 60 + minute

            if total_mins < 630:  # before 10:30
                bucket = "morning"
            elif total_mins < 780:  # before 13:00
                bucket = "midday"
            else:
                bucket = "afternoon"

            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            buckets[bucket]["trades"] += 1
            buckets[bucket]["pnl"] += trade_pnl
            if t["is_win"]:
                buckets[bucket]["wins"] += 1

        result = {}
        for period_name, data in buckets.items():
            result[period_name] = {
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl": round(data["pnl"], 2),
            }

        return result

    async def get_hourly_stats(self, user_id: uuid.UUID, period: str = "1m") -> list[dict]:
        """Win rate per hour (9-15) with trade count and P&L."""
        classified = await self.classify_trades(user_id)
        classified = self._filter_by_period(classified, period)

        hourly: dict[int, dict] = {h: {"trades": 0, "wins": 0, "pnl": 0.0} for h in range(9, 16)}

        for t in classified:
            dt = datetime.fromisoformat(t["created_at"])
            hour = dt.hour
            if hour in hourly:
                trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
                hourly[hour]["trades"] += 1
                hourly[hour]["pnl"] += trade_pnl
                if t["is_win"]:
                    hourly[hour]["wins"] += 1

        return [
            {
                "hour": h,
                "label": f"{h}:00",
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl": round(data["pnl"], 2),
            }
            for h, data in sorted(hourly.items())
        ]

    async def get_day_stats(self, user_id: uuid.UUID, period: str = "1m") -> list[dict]:
        """Win rate per day of week with trade count and P&L."""
        classified = await self.classify_trades(user_id)
        classified = self._filter_by_period(classified, period)

        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        day_data: dict[str, dict] = {d: {"trades": 0, "wins": 0, "pnl": 0.0} for d in days_order}

        for t in classified:
            dt = datetime.fromisoformat(t["created_at"])
            day_name = dt.strftime("%A")
            if day_name in day_data:
                trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
                day_data[day_name]["trades"] += 1
                day_data[day_name]["pnl"] += trade_pnl
                if t["is_win"]:
                    day_data[day_name]["wins"] += 1

        return [
            {
                "day": d,
                "short_day": d[:3],
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl": round(data["pnl"], 2),
            }
            for d in days_order
            if (data := day_data[d])
        ]

    async def get_instrument_stats(self, user_id: uuid.UUID, period: str = "1m") -> dict:
        """Win rate per instrument with trade count and avg P&L."""
        classified = await self.classify_trades(user_id)
        classified = self._filter_by_period(classified, period)

        instruments: dict[str, dict] = {}
        for t in classified:
            key = t["symbol"]
            if key not in instruments:
                instruments[key] = {"trades": 0, "wins": 0, "pnl": 0.0}
            trade_pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            instruments[key]["trades"] += 1
            instruments[key]["pnl"] += trade_pnl
            if t["is_win"]:
                instruments[key]["wins"] += 1

        result = {}
        for key, data in instruments.items():
            result[key] = {
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl": round(data["pnl"], 2),
                "avg_pnl": round(data["pnl"] / data["trades"], 2) if data["trades"] > 0 else 0,
            }

        return result

    async def get_best_worst_setups(self, user_id: uuid.UUID, period: str = "1m") -> dict:
        """Best and worst performing instrument by avg P&L."""
        stats = await self.get_instrument_stats(user_id, period)
        if not stats:
            return {"best": None, "worst": None}

        items = [{"instrument": k, **v} for k, v in stats.items()]
        best = max(items, key=lambda x: x["avg_pnl"])
        worst = min(items, key=lambda x: x["avg_pnl"])
        return {"best": best, "worst": worst}

    async def get_hold_time_analysis(self, user_id: uuid.UUID, period: str = "1m") -> dict:
        """Approximate hold time by pairing consecutive buy->sell on same symbol."""
        trades = await self.filter_trades(user_id)
        trades.reverse()  # chronological

        classified = await self.classify_trades(user_id)
        classified = self._filter_by_period(classified, period)

        winning_hold_times: list[float] = []
        losing_hold_times: list[float] = []

        by_symbol: dict[str, list[dict]] = {}
        for t in trades:
            by_symbol.setdefault(t["symbol"], []).append(t)

        for symbol, symbol_trades in by_symbol.items():
            last_buy_time = None
            for t in symbol_trades:
                if t["side"] == "buy":
                    last_buy_time = datetime.fromisoformat(t["created_at"])
                elif t["side"] == "sell" and last_buy_time is not None:
                    sell_time = datetime.fromisoformat(t["created_at"])
                    hold_minutes = (sell_time - last_buy_time).total_seconds() / 60

                    sell_classified = next(
                        (c for c in classified
                         if c["symbol"] == symbol and c["created_at"] == t["created_at"]),
                        None,
                    )
                    if sell_classified and sell_classified.get("is_win"):
                        winning_hold_times.append(hold_minutes)
                    elif sell_classified:
                        losing_hold_times.append(hold_minutes)
                    last_buy_time = None

        avg_all = winning_hold_times + losing_hold_times

        return {
            "average": round(sum(avg_all) / len(avg_all), 1) if avg_all else 0,
            "winning": round(sum(winning_hold_times) / len(winning_hold_times), 1) if winning_hold_times else 0,
            "losing": round(sum(losing_hold_times) / len(losing_hold_times), 1) if losing_hold_times else 0,
        }

    async def get_coaching_insights(self, user_id: uuid.UUID, period: str = "1m") -> dict:
        """Aggregates all analytics into a single coaching-ready payload."""
        win_rate_by_time = await self.get_win_rate_by_time(user_id, period)
        hourly_stats = await self.get_hourly_stats(user_id, period)
        day_stats = await self.get_day_stats(user_id, period)
        instrument_stats = await self.get_instrument_stats(user_id, period)
        best_worst = await self.get_best_worst_setups(user_id, period)
        hold_time = await self.get_hold_time_analysis(user_id, period)

        classified = await self.classify_trades(user_id)
        classified = self._filter_by_period(classified, period)
        total = len(classified)

        win_pnls: list[float] = []
        loss_pnls: list[float] = []
        for t in classified:
            pnl = (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            (win_pnls if t["is_win"] else loss_pnls).append(pnl)

        total_pnl = sum(win_pnls) + sum(loss_pnls)
        avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
        avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
        gross_loss = abs(sum(loss_pnls))
        profit_factor = sum(win_pnls) / gross_loss if gross_loss > 0 else 0

        # Insights from best/worst setups and time analysis
        insights: list[dict] = []
        if best_worst["best"]:
            b = best_worst["best"]
            insights.append({
                "id": "best_setup",
                "type": "positive",
                "title": f"Best instrument: {b['instrument']}",
                "description": (
                    f"Avg P&L of ₹{b['avg_pnl']:,.0f} across "
                    f"{b['trades']} trades with {b['win_rate']:.0f}% win rate."
                ),
            })
        if best_worst["worst"] and best_worst["worst"] != best_worst["best"]:
            w = best_worst["worst"]
            insights.append({
                "id": "worst_setup",
                "type": "negative",
                "title": f"Weakest instrument: {w['instrument']}",
                "description": (
                    f"Avg P&L of ₹{w['avg_pnl']:,.0f} across "
                    f"{w['trades']} trades with {w['win_rate']:.0f}% win rate."
                ),
            })
        if win_rate_by_time:
            best_time = max(
                win_rate_by_time.items(),
                key=lambda x: x[1].get("win_rate", 0),
            )
            if best_time[1].get("trades", 0) > 0:
                insights.append({
                    "id": "best_time",
                    "type": "positive",
                    "title": f"Best time: {best_time[0].capitalize()}",
                    "description": (
                        f"{best_time[1]['win_rate']:.0f}% win rate "
                        f"across {best_time[1]['trades']} trades."
                    ),
                })

        # Reshape hold_time → hold_time_analysis
        def _fmt_mins(m: float) -> str:
            if m < 60:
                return f"{round(m)} min"
            return f"{m / 60:.1f} hr"

        avg_winner_hold = hold_time.get("winning", 0)
        avg_loser_hold = hold_time.get("losing", 0)
        hold_time_analysis = {
            "avg_winner_hold": _fmt_mins(avg_winner_hold),
            "avg_loser_hold": _fmt_mins(avg_loser_hold),
            "optimal_hold": _fmt_mins(avg_winner_hold),
            "efficiency": round(
                min(avg_loser_hold, avg_winner_hold) / max(avg_loser_hold, avg_winner_hold), 2
            ) if avg_winner_hold > 0 and avg_loser_hold > 0 else 0,
            "insight": (
                f"You hold winners for {_fmt_mins(avg_winner_hold)} and "
                f"losers for {_fmt_mins(avg_loser_hold)} on average."
            ) if avg_winner_hold > 0 or avg_loser_hold > 0 else None,
        }

        return {
            "summary": {
                "total_trades": total,
                "wins": len(win_pnls),
                "losses": len(loss_pnls),
                "win_rate": round(len(win_pnls) / total * 100, 1) if total > 0 else 0,
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(total_pnl / total, 2) if total > 0 else 0,
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
            },
            "insights": insights,
            "hold_time_analysis": hold_time_analysis,
            "win_rate_by_time": win_rate_by_time,
            "hourly_stats": hourly_stats,
            "day_stats": day_stats,
            "instrument_stats": instrument_stats,
            "best_setup": best_worst["best"],
            "worst_setup": best_worst["worst"],
        }

    # -- private helpers --

    def _group_trades(self, trades: list[dict], group_by: str | None) -> dict[str, list[dict]]:
        if group_by is None:
            return {"all": trades}

        key_map = {"instrument": "symbol", "direction": "side"}
        key = key_map.get(group_by, group_by)
        groups: dict[str, list[dict]] = {}
        for t in trades:
            g = t.get(key, "unknown")
            groups.setdefault(g, []).append(t)
        return groups

    def _aggregate_count(self, trades: list[dict], group_by: str | None) -> list[dict]:
        groups = self._group_trades(trades, group_by)
        return [{"group": g, "value": len(ts)} for g, ts in groups.items()]

    def _aggregate_pnl(self, trades: list[dict], group_by: str | None) -> list[dict]:
        groups = self._group_trades(trades, group_by)
        result = []
        for g, ts in groups.items():
            buys = [t for t in ts if t["side"] == "buy"]
            sells = [t for t in ts if t["side"] == "sell"]

            total_buy_cost = sum(float(t["total"]) for t in buys)
            total_buy_qty = sum(float(t["quantity"]) for t in buys)
            avg_buy = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0

            realized_pnl = sum(
                (float(s["price"]) - avg_buy) * float(s["quantity"]) for s in sells
            )
            result.append({"group": g, "value": round(realized_pnl, 2)})
        return result

    def _aggregate_volume(self, trades: list[dict], group_by: str | None) -> list[dict]:
        groups = self._group_trades(trades, group_by)
        return [
            {"group": g, "value": round(sum(float(t["total"]) for t in ts), 2)}
            for g, ts in groups.items()
        ]

    def _aggregate_win_rate(self, trades: list[dict], group_by: str | None) -> list[dict]:
        groups = self._group_trades(trades, group_by)
        result = []
        for g, ts in groups.items():
            sells = [t for t in ts if t["side"] == "sell"]
            buys = [t for t in ts if t["side"] == "buy"]
            if not sells:
                result.append({"group": g, "value": 0.0})
                continue
            total_buy_qty = sum(float(t["quantity"]) for t in buys)
            avg_buy = sum(float(t["total"]) for t in buys) / total_buy_qty if total_buy_qty else 0
            wins = sum(1 for s in sells if float(s["price"]) > avg_buy)
            result.append({"group": g, "value": round(wins / len(sells) * 100, 2)})
        return result

    def _aggregate_avg_return(self, trades: list[dict], group_by: str | None) -> list[dict]:
        groups = self._group_trades(trades, group_by)
        result = []
        for g, ts in groups.items():
            sells = [t for t in ts if t["side"] == "sell"]
            buys = [t for t in ts if t["side"] == "buy"]
            if not sells or not buys:
                result.append({"group": g, "value": 0.0})
                continue
            total_buy_qty = sum(float(t["quantity"]) for t in buys)
            avg_buy = sum(float(t["total"]) for t in buys) / total_buy_qty if total_buy_qty else 0
            returns = [((float(s["price"]) - avg_buy) / avg_buy) * 100 for s in sells if avg_buy > 0]
            avg_ret = sum(returns) / len(returns) if returns else 0
            result.append({"group": g, "value": round(avg_ret, 2)})
        return result
