"""monthly_revenue_goal: Meta de faturamento mensal configuravel no financial_settings

Revision ID: 0033
Revises: 0032
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "financial_settings",
        sa.Column("monthly_revenue_goal", sa.Numeric(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_settings", "monthly_revenue_goal")
