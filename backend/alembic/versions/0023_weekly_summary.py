"""weekly_summary: opt-in e token de descadastro em 1 clique (A-12, V5-01/V5-02)

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Adiciona coluna weekly_summary_enabled (default True)
    op.add_column(
        "professionals",
        sa.Column(
            "weekly_summary_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    # 2. Adiciona coluna weekly_summary_token (temporariamente nullable para preencher)
    op.add_column(
        "professionals",
        sa.Column(
            "weekly_summary_token",
            sa.String(64),
            nullable=True,
        ),
    )

    # 3. Popula tokens aleatórios únicos para profissionais já existentes
    op.execute(
        """
        UPDATE professionals
        SET weekly_summary_token = md5(random()::text || clock_timestamp()::text || id::text)
        WHERE weekly_summary_token IS NULL;
        """
    )

    # 4. Torna a coluna nullable=False e adiciona indice único
    op.alter_column("professionals", "weekly_summary_token", nullable=False)
    op.create_index(
        "ix_professionals_weekly_summary_token",
        "professionals",
        ["weekly_summary_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_professionals_weekly_summary_token", table_name="professionals")
    op.drop_column("professionals", "weekly_summary_token")
    op.drop_column("professionals", "weekly_summary_enabled")
