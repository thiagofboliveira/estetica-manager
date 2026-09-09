"""procedure_supplies: Ficha técnica de insumos por procedimento e consumo automático

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "procedure_supplies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "procedure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procedures.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "supply_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False, server_default="1.00"),
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
        sa.UniqueConstraint("procedure_id", "supply_id", name="uq_procedure_supplies_procedure_supply"),
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON procedure_supplies TO estetica_app;
                END IF;
            END
            $$;
            """
        )
        op.execute("ALTER TABLE procedure_supplies ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE procedure_supplies FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON procedure_supplies
                FOR ALL
                USING (
                    professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
                )
                WITH CHECK (
                    professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
                )
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON procedure_supplies")

    op.drop_table("procedure_supplies")
