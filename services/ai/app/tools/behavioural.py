from __future__ import annotations

BEHAVIOURAL_TOOLS = [
    {
        "name": "get_alerts",
        "description": "Get active behavioural alerts for the trader (revenge trading, overtrading, drawdown warnings, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_risk_metrics",
        "description": "Get current risk metrics: drawdown %, trade velocity, concentration, today's win rate, largest loss",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_coaching_insights",
        "description": "Get performance coaching data: win rates by time of day, day of week, and instrument. Includes best/worst setups and hold time analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Analysis period: 7d, 14d, 30d",
                    "default": "30d",
                },
            },
            "required": [],
        },
    },
]
