"""Timed HTTP logging via httpx event hooks."""
from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger("app.http")


async def on_request(request: httpx.Request) -> None:
    request.extensions["start_time"] = time.perf_counter()


async def on_response(response: httpx.Response) -> None:
    elapsed = time.perf_counter() - response.request.extensions.get("start_time", 0)
    ms = elapsed * 1000
    logger.info(
        "HTTP %s %s → %d (%.0fms)",
        response.request.method,
        response.request.url,
        response.status_code,
        ms,
    )


EVENT_HOOKS: dict = {
    "request": [on_request],
    "response": [on_response],
}
