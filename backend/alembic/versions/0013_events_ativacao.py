"""events: tabela append-only de eventos de ativação (G-13) + RLS

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-05

Reproduz o esqueleto de _create_simple_tenant_table de
0003_despesas_fixas.py — mesma estrutura de tenant simples, sem FK
composta contra outra tabela além de professionals.

Escopo tenant-scoped só (ver app/models/event.py docstring): a visão
cross-clínica de funil do super-admin fica de fora nesta versão.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_simple_tenant_table(name: str, extra_columns: list[sa.Column]) -> None:
    op.create_table(
        name,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *extra_columns,
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(f"ix_{name}_professional_id", name, ["professional_id"])
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {name} TO estetica_app")
    op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {name}
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )


def upgrade() -> None:
    _create_simple_tenant_table(
        "events",
        [
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("payload", postgresql.JSONB(), nullable=True),
        ],
    )
    op.create_index("ix_events_name", "events", ["name"])


def downgrade() -> None:
    op.drop_table("events")
