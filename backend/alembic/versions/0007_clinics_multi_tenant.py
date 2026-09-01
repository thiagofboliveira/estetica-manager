"""multi_tenant: add clinics table and clinic_id FK to users and professionals

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-31

Cobre:
- BACK-06: Modelagem da Clínica e evolução Multi-Tenant SaaS
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tabela de Clínicas (Tenant Organizacional da Plataforma)
    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("document", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("plan", sa.String(), nullable=False, server_default="standard"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON clinics TO estetica_app")

    # 2. Adicionar clinic_id em users e professionals
    op.add_column(
        "users",
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_users_clinic_id", "users", ["clinic_id"])

    op.add_column(
        "professionals",
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_professionals_clinic_id", "professionals", ["clinic_id"])

    # 3. Backfill seguro: caso existam registros sem clínica, associa a uma clínica inicial padrão
    op.execute(
        """
        DO $$
        DECLARE
            default_clinic_id uuid;
        BEGIN
            IF EXISTS (SELECT 1 FROM users WHERE clinic_id IS NULL) THEN
                INSERT INTO clinics (id, name, plan, is_active, created_at, updated_at)
                VALUES (gen_random_uuid(), 'Clínica Principal', 'standard', true, now(), now())
                RETURNING id INTO default_clinic_id;

                UPDATE users SET clinic_id = default_clinic_id WHERE clinic_id IS NULL AND is_superuser = false;
                UPDATE professionals SET clinic_id = default_clinic_id WHERE clinic_id IS NULL;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_professionals_clinic_id", table_name="professionals")
    op.drop_column("professionals", "clinic_id")
    op.drop_index("ix_users_clinic_id", table_name="users")
    op.drop_column("users", "clinic_id")
    op.drop_table("clinics")
