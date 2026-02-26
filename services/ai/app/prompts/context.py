from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.be_client import BEClient

logger = logging.getLogger(__name__)


@dataclass
class PromptContext:
    """Dynamic context fetched from the BE service for system prompt injection."""

    portfolio_summary: dict = field(default_factory=dict)
    alerts: list = field(default_factory=list)
    risk_metrics: dict = field(default_factory=dict)
    coaching_insights: dict = field(default_factory=dict)
    wellbeing: dict = field(default_factory=dict)
    nifty_price: dict = field(default_factory=dict)
    banknifty_price: dict = field(default_factory=dict)


async def _safe_fetch(coro, label: str):
    """Execute a coroutine, returning None on failure instead of crashing."""
    try:
        return await coro
    except Exception:
        logger.debug(f"Failed to fetch {label}", exc_info=True)
        return None


async def fetch_prompt_context(
    be_client: BEClient,
    conversation_id: str,
) -> PromptContext:
    """Fetch all dynamic context from BE service in parallel."""
    results = await asyncio.gather(
        _safe_fetch(be_client.get_portfolio_summary(), "portfolio_summary"),
        _safe_fetch(be_client.get_alerts(), "alerts"),
        _safe_fetch(be_client.get_risk_metrics(), "risk_metrics"),
        _safe_fetch(be_client.get_coaching_insights(), "coaching_insights"),
        _safe_fetch(be_client.assess_wellbeing(conversation_id), "wellbeing"),
        _safe_fetch(be_client.get_price("NIFTY"), "nifty_price"),
        _safe_fetch(be_client.get_price("BANKNIFTY"), "banknifty_price"),
    )

    return PromptContext(
        portfolio_summary=results[0] or {},
        alerts=results[1] if isinstance(results[1], list) else (results[1] or {}).get("alerts", []),
        risk_metrics=results[2] or {},
        coaching_insights=results[3] or {},
        wellbeing=results[4] or {},
        nifty_price=results[5] or {},
        banknifty_price=results[6] or {},
    )
