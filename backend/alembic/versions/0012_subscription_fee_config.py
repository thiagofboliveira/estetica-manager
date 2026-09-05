"""add financial_settings.subscription_fee (G-09)

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-05

O ROI exibido à profissional (GET /dashboard/roi) dividia por
DEFAULT_SUBSCRIPTION_FEE = Decimal("97.00"), hardcoded em
attribution_service.py — se o preço real da assinatura for diferente
(ver docs/pending/BACKLOG_GO_LIVE.md §4.3, recomendação R$39), o número
exibido está simplesmente errado (viola I7: número exibido tem de ser
o real). Vira coluna em financial_settings — mesmo padrão de
configuração por tenant já usado ali — até existir uma tabela de
assinatura real (V2 do BACKLOG_VERSAO_COMPLETA.md).

server_default explícito: NÃO reflete o preço real do produto, é só um
valor técnico seguro para não quebrar linhas existentes — combinado com
is_estimated=True/uma nota de estimativa em toda leitura enquanto não
houver uma tabela de assinatura real (I7).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "financial_settings",
        sa.Column(
            "subscription_fee",
            sa.Numeric(12, 2, asdecimal=True),
            nullable=False,
            server_default=sa.text("39.00"),
        ),
    )


def downgrade() -> None:
    op.drop_column("financial_settings", "subscription_fee")
