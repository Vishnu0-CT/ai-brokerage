"""
Yahoo Finance API Routes - Comprehensive REST API for all Yahoo Finance features
Includes WebSocket support for real-time streaming data
"""

from __future__ import annotations

import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.services.yahoo_finance import YahooFinanceService

router = APIRouter(prefix="/api/yahoo", tags=["yahoo-finance"])

# Initialize service
yahoo_service = YahooFinanceService()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """
    Get comprehensive stock quote with 70+ metrics

    **Returns:**
    - Basic: symbol, name, price, change, open, high, low, volume
    - Valuation: beta, PE, PEG, price/book, enterprise value
    - Profitability: EPS, ROE, ROA, profit margins
    - Dividends: rate, yield, ex-dividend date
    - Financial: cash, debt, debt/equity ratio
    - Revenue: revenue, cash flow, growth metrics
    - Share Stats: outstanding, float, short interest
    - Analyst: target prices, recommendations
    - Latency: milliseconds
    """
    try:
        result = await yahoo_service.get_quote(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes")
async def get_quotes(symbols: str = Query(..., description="Comma-separated list of symbols")):
    """
    Get multiple stock quotes efficiently

    **Example:** /api/yahoo/quotes?symbols=AAPL,MSFT,GOOGL
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        result = await yahoo_service.get_quotes(symbol_list)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/{symbol}")
async def get_historical(
    symbol: str,
    period: str = Query("1mo", description="Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max"),
    interval: str = Query("1d", description="Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo")
):
    """
    Get historical OHLCV data

    **Args:**
    - symbol: Stock ticker
    - period: Time period (default: 1mo)
    - interval: Data interval (default: 1d)

    **Returns:**
    - Array of bars with timestamp, open, high, low, close, volume
    """
    try:
        result = await yahoo_service.get_historical_data(symbol, period, interval)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/{symbol}")
async def get_options(
    symbol: str,
    expiry: Optional[str] = Query(None, description="Specific expiry date (YYYY-MM-DD)"),
    include_greeks: bool = Query(False, description="Calculate Options Greeks (Delta, Gamma, Theta, Vega, Rho)")
):
    """
    Get options chain data with all available expiry dates

    **Args:**
    - symbol: Stock ticker
    - expiry: Specific expiry date (YYYY-MM-DD) - optional
    - include_greeks: Calculate Greeks using Black-Scholes (default: false)

    **Returns:**
    - expirationDates: All available expiry dates
    - selectedExpiry: Currently selected expiry
    - underlyingPrice: Current stock price
    - calls: Array of call options with strike, price, volume, OI, IV
    - puts: Array of put options
    - If include_greeks=true, each option includes: delta, gamma, theta, vega, rho
    """
    try:
        result = await yahoo_service.get_options_chain(symbol, expiry, include_greeks)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending/{region}")
async def get_trending(region: str = "US"):
    """
    Get trending stocks by region

    **Args:**
    - region: US, IN (India), GB (UK), etc.

    **Returns:**
    - Array of trending stocks with prices and metrics
    """
    try:
        result = await yahoo_service.get_trending(region)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_symbols(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(10, description="Maximum number of results")
):
    """
    Search for stock symbols

    **Args:**
    - query: Search term (ticker or company name)
    - max_results: Max results to return (default: 10)

    **Returns:**
    - Array of matching stocks with symbol, name, type, exchange
    """
    try:
        result = await yahoo_service.search_symbols(query, max_results)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{symbol}")
async def get_company_info(symbol: str):
    """
    Get detailed company information

    **Returns:**
    - Company details (name, sector, industry, website)
    - Description
    - Location
    - Employees
    """
    try:
        result = await yahoo_service.get_company_info(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{symbol}")
async def get_recommendations(symbol: str):
    """
    Get analyst recommendations history

    **Returns:**
    - Array of recent analyst recommendations with firm, grade, action
    """
    try:
        result = await yahoo_service.get_recommendations(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/{symbol}")
async def get_earnings(symbol: str):
    """
    Get earnings data and calendar

    **Returns:**
    - earningsDates: Upcoming earnings dates with estimates
    - earningsHistory: Historical earnings data
    """
    try:
        result = await yahoo_service.get_earnings(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/{symbol}")
async def get_news(
    symbol: str,
    max_items: int = Query(10, description="Maximum number of news items")
):
    """
    Get latest news for a symbol

    **Returns:**
    - Array of news items with title, publisher, link, publishedAt
    """
    try:
        result = await yahoo_service.get_news(symbol, max_items)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financials/{symbol}")
async def get_financials(symbol: str):
    """
    Get financial statements

    **Returns:**
    - incomeStatement: Income statement data
    - balanceSheet: Balance sheet data
    - cashFlow: Cash flow statement data
    """
    try:
        result = await yahoo_service.get_financials(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Market Indices endpoints
@router.get("/indices/us")
async def get_us_indices():
    """Get major US market indices"""
    try:
        symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT"]  # S&P 500, Dow, Nasdaq, Russell 2000
        result = await yahoo_service.get_quotes(symbols)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/india")
async def get_india_indices():
    """Get major Indian market indices"""
    try:
        symbols = ["^NSEI", "^NSEBANK", "^BSESN"]  # Nifty 50, Bank Nifty, Sensex
        result = await yahoo_service.get_quotes(symbols)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/all")
async def get_all_indices():
    """Get all major market indices"""
    try:
        symbols = [
            # US Indices
            "^GSPC",  # S&P 500
            "^DJI",   # Dow Jones
            "^IXIC",  # Nasdaq
            "^RUT",   # Russell 2000
            # Indian Indices
            "^NSEI",      # Nifty 50
            "^NSEBANK",   # Bank Nifty
            "^BSESN",     # Sensex
            # Global
            "^FTSE",  # FTSE 100
            "^N225",  # Nikkei 225
        ]
        result = await yahoo_service.get_quotes(symbols)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Additional data endpoints
@router.get("/holders/{symbol}")
async def get_holders(symbol: str):
    """
    Get institutional holders, mutual fund holders, and major holders

    **Returns:**
    - institutionalHolders: Top institutional investors
    - mutualFundHolders: Top mutual fund investors
    - majorHolders: Ownership breakdown (insiders, institutions, float)
    """
    try:
        result = await yahoo_service.get_holders(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insider/{symbol}")
async def get_insider_transactions(symbol: str):
    """
    Get insider transactions and roster

    **Returns:**
    - insiderTransactions: Recent insider buys/sells with dates and values
    - insiderRoster: List of company insiders with positions
    - insiderPurchases: Latest insider purchases
    """
    try:
        result = await yahoo_service.get_insider_transactions(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/splits-dividends/{symbol}")
async def get_splits_and_dividends(symbol: str):
    """
    Get historical stock splits and dividend payments

    **Returns:**
    - splits: Historical stock splits with dates and ratios
    - dividends: Historical dividend payments
    - actions: All corporate actions combined
    """
    try:
        result = await yahoo_service.get_splits_and_dividends(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyst/{symbol}")
async def get_analyst_data(symbol: str):
    """
    Get comprehensive analyst data

    **Returns:**
    - priceTargets: Current analyst price targets (low, mean, high)
    - upgradesDowngrades: Recent analyst upgrades and downgrades
    - recommendations: Recommendation trends
    """
    try:
        result = await yahoo_service.get_analyst_data(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimates/{symbol}")
async def get_estimates(symbol: str):
    """
    Get earnings and revenue estimates

    **Returns:**
    - earningsEstimate: Earnings estimates by quarter
    - revenueEstimate: Revenue estimates
    - epsTrend: EPS trend over time
    - epsRevisions: Recent EPS revisions
    - growthEstimates: Growth estimates
    """
    try:
        result = await yahoo_service.get_estimates(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/{symbol}")
async def get_calendar(symbol: str):
    """
    Get calendar events

    **Returns:**
    - calendar: Upcoming earnings dates, dividend dates, and other events
    """
    try:
        result = await yahoo_service.get_calendar(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quarterly-financials/{symbol}")
async def get_quarterly_financials(symbol: str):
    """
    Get quarterly financial statements

    **Returns:**
    - quarterlyIncomeStatement: Quarterly income statement
    - quarterlyBalanceSheet: Quarterly balance sheet
    - quarterlyCashFlow: Quarterly cash flow statement
    """
    try:
        result = await yahoo_service.get_quarterly_financials(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fast-info/{symbol}")
async def get_fast_info(symbol: str):
    """
    Get fast info - minimal latency common metrics

    **Returns:**
    - Quick access to price, market cap, volume, 52-week range
    - Optimized for low-latency real-time data
    """
    try:
        result = await yahoo_service.get_fast_info(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/isin/{symbol}")
async def get_isin(symbol: str):
    """
    Get ISIN (International Securities Identification Number)

    **Returns:**
    - isin: ISIN code
    """
    try:
        result = await yahoo_service.get_isin(symbol)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time streaming
@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time stock price streaming

    **Usage:**
    1. Connect to ws://host/api/yahoo/stream
    2. Send JSON: {"action": "subscribe", "symbols": ["AAPL", "MSFT", "GOOGL"]}
    3. Receive real-time price updates every second
    4. Send JSON: {"action": "unsubscribe", "symbols": ["AAPL"]} to unsubscribe

    **Message Format:**
    - Subscribe: {"action": "subscribe", "symbols": ["AAPL"]}
    - Unsubscribe: {"action": "unsubscribe", "symbols": ["AAPL"]}
    - Unsubscribe all: {"action": "unsubscribe_all"}
    """
    await websocket.accept()

    subscribed_symbols = set()

    try:
        while True:
            # Check for incoming messages (non-blocking)
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                data = json.loads(message)

                action = data.get("action")
                symbols = data.get("symbols", [])

                if action == "subscribe":
                    subscribed_symbols.update(symbols)
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": list(subscribed_symbols)
                    })

                elif action == "unsubscribe":
                    subscribed_symbols.difference_update(symbols)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbols": list(subscribed_symbols)
                    })

                elif action == "unsubscribe_all":
                    subscribed_symbols.clear()
                    await websocket.send_json({
                        "type": "unsubscribed_all"
                    })

            except asyncio.TimeoutError:
                pass  # No message received, continue to send updates

            # Send price updates for subscribed symbols
            if subscribed_symbols:
                try:
                    quotes = await yahoo_service.get_quotes(list(subscribed_symbols))
                    await websocket.send_json({
                        "type": "update",
                        "data": quotes,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            # Wait before next update (1 second interval)
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected. Subscribed symbols: {subscribed_symbols}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass