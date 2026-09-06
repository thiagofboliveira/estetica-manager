"""professional_avatar_and_specialty: avatar_url e specialty em professionals

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("professionals", sa.Column("avatar_url", sa.String(500), nullable=True))
    op.add_column("professionals", sa.Column("specialty", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("professionals", "specialty")
    op.drop_column("professionals", "avatar_url")
