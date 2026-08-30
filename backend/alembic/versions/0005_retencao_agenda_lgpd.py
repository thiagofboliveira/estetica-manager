"""retencao e agenda: return_opportunities + bookings + RLS

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-30

Cobre:
- T-025: Tabela return_opportunities (motor de retorno e retencao)
- T-034a: Tabela bookings (agendamento provisorio / sem venda previa)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. return_opportunities
    op.create_table(
        "return_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "procedure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procedures.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_sale_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sale_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="OPEN"),
        sa.Column("contacted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("contact_channel", sa.String(50), nullable=True),
        sa.Column("contact_status", sa.String(), nullable=True),
        sa.Column(
            "resolved_by_sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("dismissed_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
    op.create_index(
        "ix_return_opportunities_professional_id",
        "return_opportunities",
        ["professional_id"],
    )
    op.create_index(
        "ix_return_opportunities_patient_id", "return_opportunities", ["patient_id"]
    )
    op.create_index(
        "ix_return_opportunities_due_date", "return_opportunities", ["due_date"]
    )
    op.create_index(
        "ix_return_opportunities_status", "return_opportunities", ["status"]
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON return_opportunities TO estetica_app"
    )
    op.execute("ALTER TABLE return_opportunities ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE return_opportunities FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON return_opportunities
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )

    # 2. bookings
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("patient_name_hint", sa.String(255), nullable=True),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "modality", sa.String(50), nullable=False, server_default="IN_PERSON"
        ),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="SCHEDULED"),
        sa.Column(
            "sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
    op.create_index("ix_bookings_professional_id", "bookings", ["professional_id"])
    op.create_index("ix_bookings_scheduled_at", "bookings", ["scheduled_at"])
    op.create_index("ix_bookings_status", "bookings", ["status"])

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON bookings TO estetica_app")
    op.execute("ALTER TABLE bookings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE bookings FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON bookings
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("return_opportunities")
