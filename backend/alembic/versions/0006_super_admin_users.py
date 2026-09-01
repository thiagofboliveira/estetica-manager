"""super_admin: add role and is_superuser to users table

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-30

Cobre:
- BACK-01: Migração do Modelo User com role e is_superuser
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
    )
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("users", "is_superuser")
    op.drop_column("users", "role")
