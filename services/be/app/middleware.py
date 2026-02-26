from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.exceptions import (
    ConditionNotFoundError,
    DailyLossLimitBreachedError,
    InsufficientFundsError,
    InsufficientHoldingsError,
    PriceUnavailableError,
    SymbolNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InsufficientFundsError)
    async def insufficient_funds(request: Request, exc: InsufficientFundsError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(InsufficientHoldingsError)
    async def insufficient_holdings(request: Request, exc: InsufficientHoldingsError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(SymbolNotFoundError)
    async def symbol_not_found(request: Request, exc: SymbolNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(ConditionNotFoundError)
    async def condition_not_found(request: Request, exc: ConditionNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(DailyLossLimitBreachedError)
    async def daily_loss_limit_breached(request: Request, exc: DailyLossLimitBreachedError):
        return JSONResponse(status_code=403, content={"error": str(exc)})

    @app.exception_handler(PriceUnavailableError)
    async def price_unavailable(request: Request, exc: PriceUnavailableError):
        return JSONResponse(status_code=503, content={"error": str(exc)})
