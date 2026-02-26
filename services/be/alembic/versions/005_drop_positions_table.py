"""drop positions table

Revision ID: 005_drop_positions
Revises: 004_holdings_fno
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_drop_positions"
down_revision: Union[str, Sequence[str], None] = "004_holdings_fno"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_positions_user", table_name="positions")
    op.drop_table("positions")


def downgrade() -> None:
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_positions_user", "positions", ["user_id"])
