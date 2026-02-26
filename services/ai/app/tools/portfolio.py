from __future__ import annotations

PORTFOLIO_TOOLS = [
    {
        "name": "get_positions",
        "description": "Get current portfolio positions with live P&L. Optionally filter by instrument or condition (profitable, losing, options_only, equities_only).",
        "input_schema": {
            "type": "object",
            "properties": {
                "instrument": {
                    "type": "string",
                    "description": "Filter to a specific instrument symbol",
                },
                "filter": {
                    "type": "string",
                    "enum": ["profitable", "losing", "options_only", "equities_only"],
                    "description": "Filter positions by condition",
                },
            },
        },
    },
    {
        "name": "get_balance",
        "description": "Get account balance: cash available, invested value, total portfolio value, and total P&L.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "filter_trades",
        "description": "Search and filter past trades/transactions. Filter by instrument, date range, direction (buy/sell), or trade type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instrument": {
                    "type": "string",
                    "description": "Filter to trades for a specific instrument",
                },
                "date_range_start": {
                    "type": "string",
                    "description": "Start date in ISO format (e.g., 2026-02-01)",
                },
                "date_range_end": {
                    "type": "string",
                    "description": "End date in ISO format",
                },
                "direction": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "Filter by trade direction",
                },
                "trade_type": {
                    "type": "string",
                    "enum": ["equity", "option"],
                    "description": "Filter by trade type",
                },
            },
        },
    },
    {
        "name": "aggregate_metrics",
        "description": "Compute aggregated metrics across trades. Group by instrument, direction, or time period. Metrics: pnl, count, win_rate, avg_return, total_volume.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "enum": ["instrument", "direction", "day", "week"],
                    "description": "How to group the results",
                },
                "metric": {
                    "type": "string",
                    "enum": ["pnl", "count", "win_rate", "avg_return", "total_volume"],
                    "description": "Which metric to compute",
                },
                "instrument": {
                    "type": "string",
                    "description": "Optional: filter to specific instrument before aggregating",
                },
                "date_range_start": {"type": "string", "description": "Start date in ISO format (e.g., 2026-02-01)"},
                "date_range_end": {"type": "string", "description": "End date in ISO format"},
            },
            "required": ["metric"],
        },
    },
    {
        "name": "calculate_exposure",
        "description": "Calculate portfolio exposure/concentration by instrument, sector, or expiry. Shows allocation percentages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "by": {
                    "type": "string",
                    "enum": ["instrument", "sector", "expiry"],
                    "description": "Dimension to calculate exposure by",
                },
            },
            "required": ["by"],
        },
    },
    {
        "name": "simulate_scenario",
        "description": "Run a what-if scenario on current positions. Estimate P&L impact from price changes, IV changes, or time decay. Can target a specific symbol or apply to all positions. Supports both percentage and absolute point changes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Optional: restrict scenario to a specific symbol (e.g., 'NIFTY'). If omitted, applies to all positions.",
                },
                "price_change": {
                    "type": "number",
                    "description": "Fractional price change to simulate (e.g., -0.05 for -5%)",
                },
                "price_change_points": {
                    "type": "number",
                    "description": "Absolute price change in points (e.g., -200 for a 200-point drop). Takes precedence over price_change for the targeted symbol.",
                },
                "iv_change": {
                    "type": "number",
                    "description": "Absolute IV change in percentage points (e.g., 5 for +5% IV)",
                },
                "time_decay_days": {
                    "type": "number",
                    "description": "Number of days of time decay to simulate",
                },
                "correlations": {
                    "type": "boolean",
                    "description": "Include correlated holdings via beta coefficients (default true). Set false to only affect the target symbol.",
                },
            },
        },
    },
    {
        "name": "analyze_trade_patterns",
        "description": "Analyze trading behavior patterns after specific events (losses, wins, or losing streaks). Reveals whether the trader makes worse decisions after losses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": ["after_loss", "after_win", "during_streak"],
                    "description": "Type of event to analyze: after_loss (trades following a losing sell), after_win (trades following a winning sell), during_streak (trades during 2+ consecutive losses)",
                },
                "lookback_count": {
                    "type": "integer",
                    "description": "Number of recent classified trades to analyze (default 50)",
                },
                "min_loss_amount": {
                    "type": "number",
                    "description": "Only count losses >= this amount (in currency). Use when the user mentions a specific loss size, e.g. 'I just lost 40k' → 40000",
                },
            },
            "required": ["event_type"],
        },
    },
    {
        "name": "get_trading_signal",
        "description": "Get a composite 'should I be trading right now?' signal based on recent loss streak, time-of-day win rate, and session P&L. Returns caution/neutral/favorable with per-factor breakdown.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]
