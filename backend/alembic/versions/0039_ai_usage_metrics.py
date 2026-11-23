"""ai_usage_metrics: contadores de uso dos rascunhos de IA (AI-05)

Revision ID: 0039
Revises: 0038
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

COLUMNS = ("fallbacks_count", "sent_count", "edited_count")


def upgrade() -> None:
    for col in COLUMNS:
        op.add_column(
            "ai_usage",
            sa.Column(col, sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    for col in reversed(COLUMNS):
        op.drop_column("ai_usage", col)
