"""patient_photos: galeria clinica antes e depois (US-01)

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. patient_photos
    op.create_table(
        "patient_photos",
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
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
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
            "photo_type",
            sa.String(32),
            nullable=False,
            server_default="BEFORE",
        ),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("caption", sa.String(255), nullable=True),
        sa.Column(
            "captured_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "authorized_social_media",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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

    # 2. Grants para estetica_app
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'estetica_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON patient_photos TO estetica_app;
            END IF;
        END $$;
        """
    )

    # 3. RLS
    op.execute("ALTER TABLE patient_photos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE patient_photos FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON patient_photos
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
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON patient_photos")
    op.drop_table("patient_photos")
