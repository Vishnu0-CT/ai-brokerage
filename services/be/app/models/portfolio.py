from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_holdings_user_symbol"),
    )


class PortfolioConfig(Base):
    __tablename__ = "portfolio_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    initial_cash: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    current_cash: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    daily_loss_limit: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False, default=Decimal("25000")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    total_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    invested_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_snapshots_user_created", "user_id", "created_at"),
    )


class MarginConfig(Base):
    __tablename__ = "margin_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    margin_multiplier: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False, default=Decimal("1.0")
    )
    maintenance_margin_pct: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False, default=Decimal("25.0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
