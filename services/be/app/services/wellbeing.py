from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Message

logger = logging.getLogger(__name__)

PANIC_KEYWORDS = [
    "exit everything", "close it all", "sell everything", "dump everything",
    "get me out", "close all", "panic", "sab bech do", "sab exit karo",
    "sell all", "liquidate", "get out of everything", "stop everything",
    "band karo", "sab band karo", "nikalo mujhe", "loss ho raha hai",
]

CADENCE_WINDOW_SECONDS = 60
CADENCE_THRESHOLD = 5


class WellbeingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assess(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str | None = None,
        analytics_service: Any | None = None,
    ) -> dict:
        """Return {level: 'normal'|'elevated'|'high', signals: [...]}."""
        signals: list[str] = []

        # Signal 1: Panic keywords
        if user_message:
            msg_lower = user_message.lower()
            if any(kw in msg_lower for kw in PANIC_KEYWORDS):
                signals.append("panic_keywords")

        # Signal 2: Message cadence (>5 messages in <60s)
        cadence_elevated = await self._check_cadence(conversation_id)
        if cadence_elevated:
            signals.append("rapid_fire")

        # Signal 3: Session loss magnitude
        if analytics_service:
            try:
                session_loss = await self._check_session_loss(user_id, analytics_service)
                if session_loss:
                    signals.append("session_loss")
            except Exception:
                logger.debug("Could not compute session loss for wellbeing check")

        if len(signals) >= 2:
            level = "high"
        elif len(signals) >= 1:
            level = "elevated"
        else:
            level = "normal"

        return {"level": level, "signals": signals}

    async def _check_cadence(self, conversation_id: uuid.UUID) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=CADENCE_WINDOW_SECONDS)
        result = await self._session.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
            .where(Message.role == "user")
            .where(Message.created_at >= cutoff)
        )
        count = result.scalar() or 0
        return count >= CADENCE_THRESHOLD

    async def _check_session_loss(
        self, user_id: uuid.UUID, analytics_service: Any,
    ) -> bool:
        now = datetime.now(timezone.utc)
        session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        classified = await analytics_service.classify_trades(user_id)
        today_trades = [
            t for t in classified
            if datetime.fromisoformat(t["created_at"]) >= session_start
        ]

        if not today_trades:
            return False

        session_pnl = sum(
            (float(t["price"]) - t["avg_buy_price"]) * float(t["quantity"])
            for t in today_trades
        )
        # Flag if session loss exceeds 5000 (significant for a 14L portfolio)
        return session_pnl < -5000
