"""public_booking_slug_token: slug/bio em professionals e management_token/procedure_id/patient_phone em bookings

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. professionals: slug e bio
    op.add_column("professionals", sa.Column("slug", sa.String(100), nullable=True))
    op.add_column("professionals", sa.Column("bio", sa.String(1000), nullable=True))

    # Preenche slug para registros existentes garantindo formato url-friendly e unicidade
    op.execute(
        """
        UPDATE professionals
        SET slug = CONCAT(
            NULLIF(regexp_replace(regexp_replace(lower(name), '[^a-z0-9]+', '-', 'g'), '^-|-$', '', 'g'), ''),
            '-',
            SUBSTRING(id::text, 1, 6)
        )
        WHERE slug IS NULL;
        """
    )
    op.create_index("ix_professionals_slug", "professionals", ["slug"], unique=True)

    # 2. bookings: procedure_id, patient_phone, management_token
    op.add_column(
        "bookings",
        sa.Column(
            "procedure_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("procedures.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_bookings_procedure_id", "bookings", ["procedure_id"])

    op.add_column("bookings", sa.Column("patient_phone", sa.String(30), nullable=True))
    op.add_column("bookings", sa.Column("management_token", sa.String(64), nullable=True))

    op.execute(
        """
        UPDATE bookings
        SET management_token = md5(random()::text || clock_timestamp()::text || id::text)
        WHERE management_token IS NULL;
        """
    )
    op.alter_column("bookings", "management_token", nullable=False)
    op.create_index(
        "ix_bookings_management_token", "bookings", ["management_token"], unique=True
    )

    # 3. Atualiza policy de RLS em bookings para aceitar bypass_tenant e NULLIF (evita erro de cast vazio)
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON bookings")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON bookings
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
    op.drop_index("ix_bookings_management_token", table_name="bookings")
    op.drop_column("bookings", "management_token")
    op.drop_column("bookings", "patient_phone")
    op.drop_index("ix_bookings_procedure_id", table_name="bookings")
    op.drop_column("bookings", "procedure_id")

    op.drop_index("ix_professionals_slug", table_name="professionals")
    op.drop_column("professionals", "bio")
    op.drop_column("professionals", "slug")
