"""populate_missing_slugs: garante slug para todos os profissionais sem slug e heranca de role

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Garante que o role atual (ex: postgres no Supabase) herde estetica_app se ela existir
    op.execute(
        "DO $$ BEGIN EXECUTE format('GRANT estetica_app TO %I', CURRENT_USER); EXCEPTION WHEN OTHERS THEN null; END $$;"
    )

    # 2. Popula slug para qualquer profissional existente que esteja sem slug
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
