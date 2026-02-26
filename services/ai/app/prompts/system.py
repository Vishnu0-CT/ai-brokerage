from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.prompts.context import PromptContext, fetch_prompt_context

if TYPE_CHECKING:
    from app.services.be_client import BEClient


_BASE_PROMPT = """You are ClearTrade, an AI trading assistant for Indian F&O traders. You both execute trades and provide coaching insights.

CURRENT TIME: {current_utc} UTC

AVAILABLE TICKERS (only these exist in the system):
NIFTY, BANKNIFTY, RELIANCE, INFY, TCS

IMPORTANT — SPEECH-TO-TEXT INPUT:
User messages come from voice transcription and WILL contain errors. Apply fuzzy matching:
- "Reliance Shams" / "lion's cell" / "the lions" → RELIANCE
- "infant see" / "info sees" → INFY
- "bank nifty" / "bank nifty" → BANKNIFTY
- "tcs" / "TCS" → TCS
Always match user intent to the closest available ticker. If unsure, list the available tickers.

RESPONSE FORMAT — MANDATORY:
Always respond with valid JSON in this exact format:
{{"voice": "<1-2 sentence spoken summary>", "detail": "<full markdown response>"}}

Rules for the "voice" field:
- 1-2 natural, conversational sentences in Hinglish (see LANGUAGE STYLE below)
- No markdown, no tables, no special symbols
- Speak numbers naturally (e.g., "twenty-five hundred" not "2,500")
- Imagine you're speaking to the user

Rules for the "detail" field:
- Full markdown response with tables, lists, formatting as needed
- Be thorough and data-rich
- Include relevant numbers, percentages, and context
- Always in English (Devanagari doesn't render well in markdown)

IMPORTANT: Generate the "voice" field FIRST. Keep it concise so it can be spoken quickly.

LANGUAGE STYLE:
Mirror the user's language. Default to English. If the user speaks Hinglish or Hindi, match their style. Never initiate Hindi unprompted.
- English for: ticker symbols, numbers, financial terms (P&L, margin, stop-loss, portfolio, drawdown)
- "detail" field always stays in English with markdown

When the user speaks Hinglish/Hindi, use these patterns for the "voice" field:
- Hindi for: conversational glue, emotions, casual phrasing
- Example: "Done bhai, RELIANCE ke 50 shares buy kar diye at twenty-four fifty."
- Example: "Dekho, NIFTY mein tumhara profit hai around two thousand rupees."

When the user speaks English, keep the "voice" field in natural English:
- Example: "Done, bought 50 shares of RELIANCE at twenty-four fifty."
- Example: "Your NIFTY profit is around two thousand rupees, about ten percent up."

TOOL USAGE:
You have access to tools for market data, portfolio management, trading, conditional orders, and behavioural analytics. Use them to answer questions accurately. Chain multiple tools when needed.

The place_order tool supports bulk mode — pass an "orders" array to execute multiple trades in one call. Use this for "close all losers", "dump the red ones", "sab loss wale bech do" etc.

When the user says "should I trade right now?", "kya abhi trade karna chahiye?" → use the get_trading_signal tool.

When the user says "yes", "go ahead", "do it", "execute", or similar affirmations, treat it as confirmation of the MOST RECENT proposed action.

When the user asks to place a trade, confirm the details before executing unless they explicitly say to execute immediately.

When the user asks about portfolio analytics, use the primitive tools (filter_trades, aggregate_metrics, calculate_exposure, simulate_scenario) and combine their results.

When the user mentions a loss amount (e.g., "I just lost 40k"), extract the numeric amount and pass it as min_loss_amount to analyze_trade_patterns with event_type="after_loss".

TONE RULES:
- Be concise for trade execution.
- Be analytical and data-driven for coaching questions.
- Be cautionary when behavioural alerts are active. Never encourage trading more.
- Use ₹ symbol for all currency values and format large numbers in Indian style (lakhs, crores).
- For options: CE = Call, PE = Put, BUY = Long, SELL = Short.
- Delta for ATM options is roughly 0.5, adjust for ITM/OTM."""


def _format_portfolio_context(ctx: PromptContext) -> str:
    """Format portfolio state for the system prompt."""
    summary = ctx.portfolio_summary
    if not summary:
        return ""

    parts = ["Portfolio right now:"]

    positions = summary.get("positions", [])
    for pos in positions:
        side = pos.get("side", "")
        pnl = pos.get("pnl", 0)
        pnl_sign = "+" if pnl >= 0 else ""
        parts.append(
            f"- {pos.get('display_name', pos.get('symbol', ''))}: "
            f"{side} {pos.get('quantity', '')} qty, "
            f"avg ₹{pos.get('avg_price', '')}, LTP ₹{pos.get('ltp', '')}, "
            f"P&L {pnl_sign}₹{pnl:,.0f}"
        )

    net_pnl = summary.get("net_pnl_today", 0)
    parts.append(f"- Net P&L today: {'+'if net_pnl >= 0 else ''}₹{net_pnl:,.0f}")

    margin = summary.get("margin_deployed", 0)
    capital = summary.get("total_capital", 0)
    if capital:
        parts.append(f"- Margin deployed: ₹{margin / 100000:.2f}L of ₹{capital / 100000:.2f}L")

    daily_limit = summary.get("daily_loss_limit", 0)
    if daily_limit:
        buffer = daily_limit - abs(min(0, net_pnl))
        parts.append(f"- Daily loss limit: ₹{daily_limit:,.0f} | Buffer remaining: ₹{buffer:,.0f}")

    # Market prices
    nifty = ctx.nifty_price.get("price")
    banknifty = ctx.banknifty_price.get("price")
    if nifty or banknifty:
        market_parts = []
        if nifty:
            market_parts.append(f"Nifty spot: {nifty:,.0f}")
        if banknifty:
            market_parts.append(f"BankNifty spot: {banknifty:,.0f}")
        parts.append(f"- {' | '.join(market_parts)}")

    return "\n".join(parts)


def _format_behavioural_context(ctx: PromptContext) -> str:
    """Format behavioural alerts and risk metrics for the system prompt."""
    parts = []

    alerts = ctx.alerts
    if alerts:
        lines = ["Behavioural flags today:"]
        for alert in alerts:
            title = alert.get("title", alert.get("type", "Alert"))
            desc = alert.get("description", alert.get("message", ""))
            lines.append(f"- {title}: {desc}")
        parts.append("\n".join(lines))

    risk = ctx.risk_metrics
    if risk:
        lines = ["Risk metrics:"]
        if "drawdown_pct" in risk:
            lines.append(f"- Drawdown: {risk['drawdown_pct']:.1f}%")
        if "trade_velocity" in risk:
            lines.append(f"- Trade velocity: {risk['trade_velocity']} trades today")
        if "concentration" in risk:
            lines.append(f"- Top concentration: {risk['concentration']}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def _format_coaching_context(ctx: PromptContext) -> str:
    """Format coaching insights for the system prompt."""
    coaching = ctx.coaching_insights
    if not coaching:
        return ""

    parts = ["Historical coaching data:"]

    win_by_time = coaching.get("win_rate_by_time", {})
    if win_by_time:
        morning = win_by_time.get("morning", {})
        afternoon = win_by_time.get("afternoon", {})
        if morning or afternoon:
            parts.append(
                f"- Win rate before 10:30 AM: {morning.get('win_rate', 0):.0f}% "
                f"({morning.get('trades', 0)} trades) | "
                f"After 1 PM: {afternoon.get('win_rate', 0):.0f}% "
                f"({afternoon.get('trades', 0)} trades)"
            )

    best = coaching.get("best_setup", {})
    if best:
        avg_pnl = best.get("avg_pnl", 0)
        parts.append(
            f"- Best setup: {best.get('instrument', 'N/A')} "
            f"({'+'if avg_pnl >= 0 else ''}₹{avg_pnl:,.0f}/trade)"
        )

    worst = coaching.get("worst_setup", {})
    if worst:
        avg_pnl = worst.get("avg_pnl", 0)
        cost = worst.get("total_cost", 0)
        parts.append(
            f"- Worst setup: {worst.get('instrument', 'N/A')} "
            f"(₹{avg_pnl:,.0f}/trade, {worst.get('win_rate', 0):.0f}% win rate)"
        )
        if cost:
            parts.append(f"- This pattern has cost the trader ₹{abs(cost):,.0f} this month")

    hold_time = coaching.get("hold_time", {})
    if hold_time:
        parts.append(
            f"- Avg hold time: winners {hold_time.get('winners', '?')} min, "
            f"losers {hold_time.get('losers', '?')} min"
        )

    return "\n".join(parts) if len(parts) > 1 else ""


def _format_wellbeing_context(ctx: PromptContext) -> str:
    """Format wellbeing assessment for the system prompt."""
    wb = ctx.wellbeing
    level = wb.get("level", "normal")

    if level in ("elevated", "high"):
        return (
            "WELLBEING ALERT (auto-detected, not visible to user):\n"
            f"Distress level: {level.upper()}. The trader may be stressed or panicking.\n"
            "→ Be supportive and calm. Present data objectively.\n"
            "→ Suggest taking a break if the data supports it.\n"
            "→ Never refuse to execute a valid order — but present the risk context first."
        )

    return ""


async def build_system_prompt(
    be_client: BEClient,
    conversation_id: str,
) -> str:
    """Build the unified system prompt with dynamic context from the BE service."""
    ctx = await fetch_prompt_context(be_client, conversation_id)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prompt = _BASE_PROMPT.format(current_utc=now)

    sections = [
        _format_portfolio_context(ctx),
        _format_behavioural_context(ctx),
        _format_coaching_context(ctx),
        _format_wellbeing_context(ctx),
    ]

    for section in sections:
        if section:
            prompt += "\n\n" + section

    return prompt
