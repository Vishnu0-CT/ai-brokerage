from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request

router = APIRouter(prefix="/api/market", tags=["market"])


def get_price_service(request: Request):
    return request.app.state.price_service


@router.get("/price/{symbol}")
async def get_price(symbol: str, svc=Depends(get_price_service)):
    tick = await svc.get_price(symbol.upper())
    if tick is None:
        raise HTTPException(status_code=404, detail=f"No price data for {symbol}")
    return {"symbol": tick.symbol, "price": tick.price, "high": tick.high, "low": tick.low}


@router.get("/quote/{symbol}")
async def get_quote(symbol: str, svc=Depends(get_price_service)):
    tick = await svc.get_quote(symbol.upper())
    if tick is None:
        raise HTTPException(status_code=404, detail=f"No quote data for {symbol}")
    return {
        "symbol": tick.symbol, "price": tick.price,
        "bid": tick.bid, "ask": tick.ask,
        "volume": tick.volume, "high": tick.high, "low": tick.low,
    }


@router.get("/history/{symbol}")
async def get_history(symbol: str, svc=Depends(get_price_service), period: str = Query("1m")):
    bars = await svc.get_history(symbol.upper(), period)
    return {"symbol": symbol.upper(), "bars": [asdict(b) for b in bars]}
