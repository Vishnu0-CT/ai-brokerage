"""add side column to holdings

Revision ID: 003_holding_side
Revises: 002_trades_strategies
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_holding_side"
down_revision: Union[str, Sequence[str], None] = "002_trades_strategies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("holdings", sa.Column("side", sa.String(), server_default="long", nullable=False))


def downgrade() -> None:
    op.drop_column("holdings", "side")
