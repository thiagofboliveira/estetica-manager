"""populate_missing_slugs: garante slug para todos os profissionais sem slug

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
    op.execute(
        """
        UPDATE professionals
        SET slug = CONCAT(
            COALESCE(NULLIF(regexp_replace(regexp_replace(lower(name), '[^a-z0-9]+', '-', 'g'), '^-|-$', '', 'g'), ''), 'agenda'),
            '-',
            SUBSTRING(id::text, 1, 6)
        )
        WHERE slug IS NULL OR slug = '';
        """
    )


def downgrade() -> None:
    pass
