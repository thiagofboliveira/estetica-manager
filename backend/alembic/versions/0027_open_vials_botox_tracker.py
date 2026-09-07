"""open_vials_botox_tracker: Rastreamento inteligente de frascos abertos de Botox e insumos perecíveis (US-03)

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. open_vials
    op.create_table(
        "open_vials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "procedure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procedures.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "medication_name",
            sa.String(255),
            nullable=False,
            server_default="Toxina Botulínica",
        ),
        sa.Column("lot_number", sa.String(100), nullable=True),
        sa.Column(
            "total_units",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="100.00",
        ),
        sa.Column(
            "used_units",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "unit_measure",
            sa.String(20),
            nullable=False,
            server_default="U",
        ),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "opened_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp() + interval '30 days'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
    )

    op.create_index("ix_open_vials_status", "open_vials", ["status"])

    # 2. Grants para estetica_app
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'estetica_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON open_vials TO estetica_app;
            END IF;
        END $$;
        """
    )

    # 3. RLS
    op.execute("ALTER TABLE open_vials ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE open_vials FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON open_vials
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON open_vials")
    op.drop_table("open_vials")
