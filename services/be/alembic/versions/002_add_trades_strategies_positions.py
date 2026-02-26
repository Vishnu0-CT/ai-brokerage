"""add trades, strategies, positions, and watchlist tables

Revision ID: 002_trades_strategies
Revises: 001_initial
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_trades_strategies"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. trades - Enhanced trade history with behavioral patterns
    op.create_table(
        "trades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time", sa.String(), nullable=False),
        sa.Column("instrument", sa.String(), nullable=False),
        sa.Column("trade_type", sa.String(), nullable=False),
        sa.Column("entry_price", sa.Numeric(), nullable=False),
        sa.Column("exit_price", sa.Numeric(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("pnl", sa.Numeric(), nullable=False),
        sa.Column("pnl_percent", sa.Numeric(), nullable=False),
        sa.Column("hold_time_minutes", sa.Integer(), nullable=False),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_revenge_trade", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_overtrade", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_tilt_trade", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_user_date", "trades", ["user_id", "date"])
    op.create_index("ix_trades_user_strategy", "trades", ["user_id", "strategy"])

    # 2. positions - Open positions
    op.create_table(
        "positions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("position_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("lots", sa.Integer(), nullable=False),
        sa.Column("avg_price", sa.Numeric(), nullable=False),
        sa.Column("expiry", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_positions_user", "positions", ["user_id"])

    # 3. strategies - Trading strategies
    op.create_table(
        "strategies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="paper_trading"),
        sa.Column("entry_conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("exit_conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("stop_loss", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("target", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("position_size", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("max_positions", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("paper_trading_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("natural_language_input", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategies_user", "strategies", ["user_id"])
    op.create_index("ix_strategies_user_status", "strategies", ["user_id", "status"])

    # 4. strategy_versions - Version history for strategies
    op.create_table(
        "strategy_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("strategy_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategy_versions_strategy", "strategy_versions", ["strategy_id"])

    # 5. watchlist_items - User watchlist
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("instrument_type", sa.String(), nullable=False),
        sa.Column("lot_size", sa.Integer(), nullable=False),
        sa.Column("tick_size", sa.Numeric(), nullable=False, server_default=sa.text("0.05")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_watchlist_user", "watchlist_items", ["user_id"])
    op.create_index("ix_watchlist_user_order", "watchlist_items", ["user_id", "display_order"])


def downgrade() -> None:
    op.drop_index("ix_watchlist_user_order", table_name="watchlist_items")
    op.drop_index("ix_watchlist_user", table_name="watchlist_items")
    op.drop_table("watchlist_items")

    op.drop_index("ix_strategy_versions_strategy", table_name="strategy_versions")
    op.drop_table("strategy_versions")

    op.drop_index("ix_strategies_user_status", table_name="strategies")
    op.drop_index("ix_strategies_user", table_name="strategies")
    op.drop_table("strategies")

    op.drop_index("ix_positions_user", table_name="positions")
    op.drop_table("positions")

    op.drop_index("ix_trades_user_strategy", table_name="trades")
    op.drop_index("ix_trades_user_date", table_name="trades")
    op.drop_table("trades")
