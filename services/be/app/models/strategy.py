from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from typing import List


class Strategy(Base):
    """Represents a trading strategy with entry/exit conditions."""
    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="paper_trading")  # active, paused, paper_trading
    
    # Entry conditions
    entry_conditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    
    # Exit conditions
    exit_conditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    
    # Risk management
    stop_loss: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    target: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    position_size: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    max_positions: Mapped[int] = mapped_column(default=1)
    
    # Paper trading stats
    paper_trading_stats: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Natural language input (for editing)
    natural_language_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationship to versions with cascade delete
    versions: Mapped[list["StrategyVersion"]] = relationship(
        "StrategyVersion",
        back_populates="strategy",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_strategies_user", "user_id"),
        Index("ix_strategies_user_status", "user_id", "status"),
    )


class StrategyVersion(Base):
    """Tracks version history of strategies."""
    __tablename__ = "strategy_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    strategy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(default=1)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Full strategy state at this version
    
    # Relationship back to strategy
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="versions")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_strategy_versions_strategy", "strategy_id"),
    )
