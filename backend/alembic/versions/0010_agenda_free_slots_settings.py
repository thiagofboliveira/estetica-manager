"""add work window settings for free slots (Épico A — Modo Ocupado)

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-02

Cobre: janela de trabalho, duração de slot e buffer usados para
calcular horários livres a sugerir no WhatsApp (roadmap 2026-09-02).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "financial_settings",
        sa.Column(
            "work_start_time",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'08:00:00'"),
        ),
    )
    op.add_column(
        "financial_settings",
        sa.Column(
            "work_end_time",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'18:00:00'"),
        ),
    )
    op.add_column(
        "financial_settings",
        sa.Column(
            "slot_duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("30"),
        ),
    )
    op.add_column(
        "financial_settings",
        sa.Column(
            "buffer_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("15"),
        ),
    )


def downgrade() -> None:
    op.drop_column("financial_settings", "buffer_minutes")
    op.drop_column("financial_settings", "slot_duration_minutes")
    op.drop_column("financial_settings", "work_end_time")
    op.drop_column("financial_settings", "work_start_time")
