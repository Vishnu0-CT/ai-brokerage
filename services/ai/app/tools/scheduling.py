from __future__ import annotations

SCHEDULING_TOOLS = [
    {
        "name": "create_conditional_order",
        "description": "Create an order that triggers when a condition is met. Conditions: price_above, price_below (triggers on price), time_at, time_after (triggers at a time), portfolio_drawdown, portfolio_concentration (triggers on portfolio state).",
        "input_schema": {
            "type": "object",
            "properties": {
                "condition_type": {
                    "type": "string",
                    "enum": ["price_above", "price_below", "time_at", "time_after", "portfolio_drawdown", "portfolio_concentration"],
                    "description": "The type of condition to monitor",
                },
                "parameters": {
                    "type": "object",
                    "description": "Condition parameters. For price: {symbol, threshold}. For time: {datetime}. For portfolio: {percentage}.",
                },
                "action": {
                    "type": "object",
                    "description": "The order to place when triggered: {side, symbol, quantity}",
                },
            },
            "required": ["condition_type", "parameters", "action"],
        },
    },
    {
        "name": "create_price_alert",
        "description": "Create an alert that notifies when a stock reaches a target price. Does NOT place a trade — only alerts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The ticker symbol to watch",
                },
                "target_price": {
                    "type": "number",
                    "description": "The price at which to trigger the alert",
                },
                "direction": {
                    "type": "string",
                    "enum": ["above", "below"],
                    "description": "Alert when price goes above or below target",
                },
            },
            "required": ["symbol", "target_price", "direction"],
        },
    },
    {
        "name": "list_active_conditions",
        "description": "List all active conditional orders and price alerts.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]
