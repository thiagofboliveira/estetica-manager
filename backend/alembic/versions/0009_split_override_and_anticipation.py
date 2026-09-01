"""add procedure split_override and financial anticipation

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-31

Cobre:
- BACK-S3-01: Coluna split_override em procedures (EPIC-S3-01 / E6)
- BACK-S3-13: Colunas de antecipação de recebíveis em financial_settings (EPIC-S3-04 / E7)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "procedures",
        sa.Column(
            "split_override",
            sa.Numeric(5, 2),
            nullable=True,
        ),
    )
    op.add_column(
        "financial_settings",
        sa.Column(
            "anticipates_all",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "financial_settings",
        sa.Column(
            "anticipation_rate_per_installment",
            sa.Numeric(5, 2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("financial_settings", "anticipation_rate_per_installment")
    op.drop_column("financial_settings", "anticipates_all")
    op.drop_column("procedures", "split_override")
