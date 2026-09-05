"""return_opportunities.source: marcar origem da oportunidade (SYSTEM vs IMPORT) (G-12)

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-05

G-12: Import gerar oportunidades de retorno retroativas. Oportunidades importadas
têm source='IMPORT' para garantir que NUNCA contem como receita atribuível ao
sistema (conservadorismo de atribuição, §18.1). Oportunidades nativas do motor
têm source='SYSTEM'.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "return_opportunities",
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
            server_default="SYSTEM",
        ),
    )
    op.create_index(
        "ix_return_opportunities_source",
        "return_opportunities",
        ["source"],
    )


def downgrade() -> None:
    op.drop_index("ix_return_opportunities_source", table_name="return_opportunities")
    op.drop_column("return_opportunities", "source")
