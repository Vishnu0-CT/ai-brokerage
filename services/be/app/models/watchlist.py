from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WatchlistItem(Base):
    """Represents an item in the user's watchlist."""
    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    instrument_type: Mapped[str] = mapped_column(String, nullable=False)  # "INDEX" or "STOCK"
    lot_size: Mapped[int] = mapped_column(Integer, nullable=False)
    tick_size: Mapped[float] = mapped_column(Numeric, nullable=False, default=0.05)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_watchlist_user", "user_id"),
        Index("ix_watchlist_user_order", "user_id", "display_order"),
    )
