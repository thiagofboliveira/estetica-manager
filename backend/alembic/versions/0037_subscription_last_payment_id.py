"""subscription_last_payment_id: deduplicar reentrega de webhook do Asaas

Revision ID: 0037
Revises: 0036
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Id da última cobrança já processada: o Asaas reentrega eventos e sem
    # isto cada reentrega de PAYMENT_CONFIRMED estendia o período de novo.
    op.add_column(
        "subscriptions",
        sa.Column("last_payment_id", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "last_payment_id")
