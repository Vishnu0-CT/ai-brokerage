"""
AI Context Service

Generates comprehensive trading data context for AI system prompts.
Includes trade history analytics, behavioral patterns, and strategy performance.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trade_history import TradeHistoryService


class AIContextService:
    """Service for generating AI context with comprehensive trading data."""
    
    def __init__(self, session: AsyncSession, price_service: Any = None) -> None:
        self._session = session
        self._price_service = price_service
        self._trade_history_service = TradeHistoryService(session)
    
    async def get_system_prompt_context(self, user_id: uuid.UUID) -> dict:
        """
        Get comprehensive context for AI system prompt.
        
        Returns:
            Dict containing all trading statistics, behavioral analysis,
            strategy performance, and risk metrics.
        """
        # Get trade summary
        trade_summary = await self._trade_history_service.get_trade_summary_for_ai(user_id)
        
        # Get analytics for different periods
        analytics_30d = await self._trade_history_service.calculate_analytics(user_id, days=30)
        analytics_60d = await self._trade_history_service.calculate_analytics(user_id, days=60)
        analytics_90d = await self._trade_history_service.calculate_analytics(user_id, days=90)
        
        return {
            "trade_summary": trade_summary,
            "analytics_30d": analytics_30d,
            "analytics_60d": analytics_60d,
            "analytics_90d": analytics_90d,
        }
    
    async def generate_system_prompt_section(self, user_id: uuid.UUID) -> str:
        """
        Generate the trading data section for the AI system prompt.
        
        Returns:
            Formatted string to be included in the system prompt.
        """
        context = await self.get_system_prompt_context(user_id)
        
        sections = []
        
        # Overall Statistics Section
        stats = context["trade_summary"]["overall_stats"]
        sections.append(self._format_overall_stats(stats))
        
        # Behavioral Analysis Section
        sections.append(self._format_behavioral_stats(stats))
        
        # Strategy Performance Section
        strategy_perf = context["trade_summary"]["strategy_performance"]
        sections.append(self._format_strategy_performance(strategy_perf))
        
        # Weekly P&L Trends Section
        weekly_pnl = context["trade_summary"]["weekly_pnl"]
        sections.append(self._format_weekly_trends(weekly_pnl))
        
        # Risk Metrics Section
        risk_metrics = context["trade_summary"]["risk_metrics"]
        sections.append(self._format_risk_metrics(risk_metrics))
        
        # Recent Patterns Section
        patterns = context["trade_summary"]["recent_patterns"]
        sections.append(self._format_recent_patterns(patterns))
        
        # Period Comparison
        sections.append(self._format_period_comparison(
            context["analytics_30d"],
            context["analytics_60d"],
            context["analytics_90d"],
        ))
        
        return "\n\n".join(filter(None, sections))
    
    def _format_overall_stats(self, stats: dict) -> str:
        """Format overall trading statistics."""
        if not stats or stats.get("total_trades", 0) == 0:
            return ""
        
        lines = [
            "TRADING STATISTICS (Overall):",
            f"- Total Trades: {stats['total_trades']}",
            f"- Win Rate: {stats['win_rate']:.1f}% ({stats['winning_trades']} wins, {stats['losing_trades']} losses)",
            f"- Total P&L: ₹{stats['total_pnl']:,.0f}",
            f"- Average P&L per Trade: ₹{stats['avg_pnl']:,.0f}",
            f"- Average Win: ₹{stats['avg_win']:,.0f} | Average Loss: ₹{stats['avg_loss']:,.0f}",
            f"- Max Win: ₹{stats['max_win']:,.0f} | Max Loss: ₹{stats['max_loss']:,.0f}",
            f"- Profit Factor: {stats['profit_factor']:.2f}",
            f"- Max Consecutive Wins: {stats['max_consecutive_wins']} | Max Consecutive Losses: {stats['max_consecutive_losses']}",
        ]
        
        return "\n".join(lines)
    
    def _format_behavioral_stats(self, stats: dict) -> str:
        """Format behavioral analysis statistics."""
        if not stats:
            return ""
        
        lines = ["BEHAVIORAL ANALYSIS:"]
        
        # Revenge trading
        if stats.get("revenge_trade_count", 0) > 0:
            lines.append(
                f"- Revenge Trades: {stats['revenge_trade_count']} trades, "
                f"Loss: ₹{abs(stats['revenge_trade_loss']):,.0f}"
            )
            lines.append("  ⚠️ Trader shows revenge trading pattern after big losses")
        
        # Overtrading
        if stats.get("overtrade_days", 0) > 0:
            lines.append(
                f"- Overtrading Days: {stats['overtrade_days']} days, "
                f"Impact: ₹{stats['overtrade_impact']:,.0f}"
            )
            lines.append("  ⚠️ Trader tends to overtrade (20+ trades/day) with diminishing returns")
        
        # Tilt trading
        if stats.get("tilt_trade_count", 0) > 0:
            lines.append(
                f"- Tilt/Emotional Trades: {stats['tilt_trade_count']} trades, "
                f"Loss: ₹{abs(stats['tilt_trade_loss']):,.0f}"
            )
            lines.append("  ⚠️ Trader abandons strategy after consecutive losses")
        
        # Time patterns
        lines.append(f"- Best Trading Hour: {stats.get('best_trading_hour', 'N/A')}")
        lines.append(f"- Worst Trading Hour: {stats.get('worst_trading_hour', 'N/A')}")
        lines.append(f"- Best Trading Day: {stats.get('best_trading_day', 'N/A')}")
        lines.append(f"- Worst Trading Day: {stats.get('worst_trading_day', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_strategy_performance(self, strategies: list[dict]) -> str:
        """Format strategy performance breakdown."""
        if not strategies:
            return ""
        
        lines = ["STRATEGY PERFORMANCE:"]
        
        for strat in strategies[:8]:  # Top 8 strategies
            emoji = "✅" if strat["total_pnl"] > 0 else "❌"
            lines.append(
                f"{emoji} {strat['strategy']}:\n"
                f"   Trades: {strat['trades']} | Win Rate: {strat['win_rate']:.0f}% | "
                f"Avg P&L: ₹{strat['avg_pnl']:,.0f} | Total: ₹{strat['total_pnl']:,.0f}"
            )
        
        return "\n".join(lines)
    
    def _format_weekly_trends(self, weekly_data: list[dict]) -> str:
        """Format weekly P&L trends."""
        if not weekly_data:
            return ""
        
        lines = ["WEEKLY P&L TRENDS (Last 10 weeks):"]
        
        for week in weekly_data[-10:]:
            emoji = "📈" if week["pnl"] > 0 else "📉"
            lines.append(
                f"{emoji} {week['week_start']} to {week['week_end']}: "
                f"₹{week['pnl']:,.0f} ({week['trades']} trades, {week['win_rate']:.0f}% win rate)"
            )
        
        # Trend analysis
        if len(weekly_data) >= 4:
            recent_4 = weekly_data[-4:]
            recent_pnl = sum(w["pnl"] for w in recent_4)
            if len(weekly_data) >= 8:
                prev_4 = weekly_data[-8:-4]
                prev_pnl = sum(w["pnl"] for w in prev_4)
                
                if recent_pnl > prev_pnl:
                    lines.append("→ Trend: IMPROVING (recent 4 weeks better than previous 4)")
                elif recent_pnl < prev_pnl:
                    lines.append("→ Trend: DECLINING (recent 4 weeks worse than previous 4)")
                else:
                    lines.append("→ Trend: STABLE")
        
        return "\n".join(lines)
    
    def _format_risk_metrics(self, risk: dict) -> str:
        """Format risk metrics."""
        if not risk:
            return ""
        
        lines = [
            "RISK METRICS:",
            f"- Max Drawdown: ₹{risk.get('max_drawdown', 0):,.0f} ({risk.get('max_drawdown_percent', 0):.1f}%)",
            f"- Longest Loss Streak: {risk.get('max_consecutive_losses', 0)} trades",
            f"- Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}",
        ]
        
        # Risk assessment
        drawdown_pct = risk.get("max_drawdown_percent", 0)
        if drawdown_pct > 20:
            lines.append("⚠️ HIGH RISK: Drawdown exceeds 20% - suggest reducing position sizes")
        elif drawdown_pct > 10:
            lines.append("⚠️ MODERATE RISK: Drawdown between 10-20% - monitor closely")
        
        return "\n".join(lines)
    
    def _format_recent_patterns(self, patterns: dict) -> str:
        """Format recently detected patterns."""
        if not patterns:
            return ""
        
        lines = ["RECENT PATTERN ALERTS:"]
        
        revenge = patterns.get("revenge_trading", {})
        if revenge and revenge.get("detected"):
            lines.append(
                f"🚨 REVENGE TRADING DETECTED: {revenge.get('message', '')}\n"
                f"   Trigger loss: ₹{abs(revenge.get('trigger_loss', 0)):,.0f}, "
                f"Subsequent loss rate: {revenge.get('subsequent_loss_rate', 0):.0f}%"
            )
        
        overtrade = patterns.get("overtrading", {})
        if overtrade and overtrade.get("total_days", 0) > 0:
            lines.append(
                f"⚠️ OVERTRADING PATTERN: {overtrade['total_days']} days with 20+ trades\n"
                f"   Total impact: ₹{overtrade.get('total_impact', 0):,.0f}"
            )
        
        if len(lines) == 1:
            lines.append("✅ No concerning patterns detected recently")
        
        return "\n".join(lines)
    
    def _format_period_comparison(
        self,
        stats_30d: dict,
        stats_60d: dict,
        stats_90d: dict,
    ) -> str:
        """Format period comparison."""
        if not stats_30d or stats_30d.get("total_trades", 0) == 0:
            return ""
        
        lines = ["PERIOD COMPARISON:"]
        
        lines.append(
            f"- Last 30 days: {stats_30d['total_trades']} trades, "
            f"{stats_30d['win_rate']:.0f}% win rate, ₹{stats_30d['total_pnl']:,.0f} P&L"
        )
        
        if stats_60d and stats_60d.get("total_trades", 0) > 0:
            lines.append(
                f"- Last 60 days: {stats_60d['total_trades']} trades, "
                f"{stats_60d['win_rate']:.0f}% win rate, ₹{stats_60d['total_pnl']:,.0f} P&L"
            )
        
        if stats_90d and stats_90d.get("total_trades", 0) > 0:
            lines.append(
                f"- Last 90 days: {stats_90d['total_trades']} trades, "
                f"{stats_90d['win_rate']:.0f}% win rate, ₹{stats_90d['total_pnl']:,.0f} P&L"
            )
        
        return "\n".join(lines)


def generate_full_system_prompt(
    base_prompt: str,
    trading_context: str,
    portfolio_context: str = "",
    alerts_context: str = "",
) -> str:
    """
    Generate the full system prompt with all context sections.
    
    Args:
        base_prompt: The base system prompt template
        trading_context: Trading statistics and behavioral analysis
        portfolio_context: Current portfolio state
        alerts_context: Active alerts and warnings
    
    Returns:
        Complete system prompt string
    """
    sections = [base_prompt]
    
    if trading_context:
        sections.append(trading_context)
    
    if portfolio_context:
        sections.append(portfolio_context)
    
    if alerts_context:
        sections.append(alerts_context)
    
    return "\n\n".join(sections)
