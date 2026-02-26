from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trade(Base):
    """Represents a completed trade with entry and exit."""
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time: Mapped[str] = mapped_column(String, nullable=False)  # HH:MM:SS format
    instrument: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "NIFTY 26500 CE"
    trade_type: Mapped[str] = mapped_column(String, nullable=False)  # "BUY" or "SELL"
    entry_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    pnl_percent: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    hold_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    strategy: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_revenge_trade: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_overtrade: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_tilt_trade: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_trades_user_date", "user_id", "date"),
        Index("ix_trades_user_strategy", "user_id", "strategy"),
    )


class Position(Base):
    """Represents an open position (not yet exited)."""
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "NIFTY 26500 CE"
    position_type: Mapped[str] = mapped_column(String, nullable=False)  # "BUY" or "SELL"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    lots: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    expiry: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "2026-02-27"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_positions_user", "user_id"),
    )
