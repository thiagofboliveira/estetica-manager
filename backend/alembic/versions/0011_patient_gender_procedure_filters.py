"""add patients.gender, procedures.is_invasive, procedures.session_plan (E1/E2)

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-03

Filtros de pacientes (sexo) e procedimentos (invasivo, sessão
única/múltipla) pedidos pelo usuário — ver docs/pending/BACKLOG_FILTROS_E_LAYOUT.md.
gender é nullable: a base já tem pacientes cadastrados sem esse dado,
forçar preenchimento retroativo não é realista. session_plan é rótulo
informativo no catálogo, desacoplado de pacotes/SaleItem de propósito.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("gender", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "procedures",
        sa.Column(
            "is_invasive",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "procedures",
        sa.Column(
            "session_plan",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'SINGLE'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("procedures", "session_plan")
    op.drop_column("procedures", "is_invasive")
    op.drop_column("patients", "gender")
