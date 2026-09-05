"""procedure_image_url: adiciona image_url na tabela procedures

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("procedures", sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("procedures", "image_url")
