"""sales: split_amount_applied + fee_amount_charged_applied

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-29

Faltavam para o ranking de procedimentos (TASK-024, MVP v7.1) funcionar:
só existia o PERCENTUAL de split (split_applied) e a taxa TOTAL da
transação (fee_amount_applied, que ignora fee_payer). Ratear split/taxa
entre itens exige o valor em R$ efetivamente aplicado. Mesmo princípio
de congelamento (I3) dos demais campos do snapshot.

Populado via backfill=0.00 para linhas existentes (dados de teste no
ambiente de dev — não há venda de produção a preservar ainda).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sales",
        sa.Column(
            "split_amount_applied",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
    )
    op.add_column(
        "sales",
        sa.Column(
            "fee_amount_charged_applied",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("sales", "fee_amount_charged_applied")
    op.drop_column("sales", "split_amount_applied")
