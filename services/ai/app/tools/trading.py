from __future__ import annotations

TRADING_TOOLS = [
    {
        "name": "place_order",
        "description": "Place one or more buy/sell orders. For a single order, use symbol/side/quantity directly. For bulk operations (e.g., closing all losers), use the 'orders' array. If price is omitted on any order, uses current market price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The ticker symbol to trade (single order mode)",
                },
                "side": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "Whether to buy or sell (single order mode)",
                },
                "quantity": {
                    "type": "number",
                    "description": "Number of shares/units to trade (single order mode)",
                },
                "price": {
                    "type": "number",
                    "description": "Price per share. If omitted, uses current market price.",
                },
                "orders": {
                    "type": "array",
                    "description": "Bulk mode: array of orders. Each item has {symbol, side, quantity, price?}. When provided, top-level symbol/side/quantity are ignored.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "side": {"type": "string", "enum": ["buy", "sell"]},
                            "quantity": {"type": "number"},
                            "price": {"type": "number"},
                        },
                        "required": ["symbol", "side", "quantity"],
                    },
                },
            },
        },
    },
    {
        "name": "cancel_conditional_order",
        "description": "Cancel an active conditional order by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The UUID of the conditional order to cancel",
                },
            },
            "required": ["order_id"],
        },
    },
]
