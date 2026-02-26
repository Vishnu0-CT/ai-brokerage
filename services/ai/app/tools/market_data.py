from __future__ import annotations

MARKET_DATA_TOOLS = [
    {
        "name": "search_tickers",
        "description": (
            "Search for available tickers by symbol or company name. "
            "Use this to validate or find tickers before placing trades or fetching prices. "
            "Accepts partial matches (e.g., 'RELI' finds RELIANCE, 'HDFC' finds HDFCBANK). "
            "Returns matching symbols with name, type, and lot size."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term — a ticker symbol, company name, or partial match",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_price",
        "description": "Get the current price of a stock or instrument. Returns price, change, and change percentage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The ticker symbol (e.g., RELIANCE, BANKNIFTY, NIFTY)",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_quote",
        "description": "Get a detailed quote for a stock including price, bid, ask, volume, and day high/low.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The ticker symbol",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_price_history",
        "description": "Get historical price data for a stock over a given period. Returns daily OHLCV bars.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The ticker symbol",
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "1w", "1m", "3m"],
                    "description": "The time period for historical data",
                },
            },
            "required": ["symbol"],
        },
    },
]
