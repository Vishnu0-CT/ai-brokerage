"""add F&O columns to holdings

Revision ID: 004_holdings_fno
Revises: 003_holding_side
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_holdings_fno"
down_revision: Union[str, Sequence[str], None] = "003_holding_side"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("holdings", sa.Column("lots", sa.Integer(), nullable=True))
    op.add_column("holdings", sa.Column("expiry", sa.String(), nullable=True))
    op.add_column("holdings", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True))


def downgrade() -> None:
    op.drop_column("holdings", "created_at")
    op.drop_column("holdings", "expiry")
    op.drop_column("holdings", "lots")
