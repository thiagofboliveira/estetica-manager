"""return_opportunities + índice de sessions.completed_at + RLS

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-01

⚠️ Gerada manualmente (sem acesso de rede a Postgres neste ambiente de
dev). Revisar contra app/models/return_opportunity.py antes de aplicar.

Cobre T-025 (MVP v7.1 §14, EPIC-10). patients e procedures não tinham
UniqueConstraint(id, professional_id) até agora (nenhuma tabela
referenciava elas via FK composta) — esta migration adiciona antes de
criar return_opportunities, que referencia as duas.
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
    op.create_unique_constraint(
        "uq_patients_id_professional", "patients", ["id", "professional_id"]
    )
    op.create_unique_constraint(
        "uq_procedures_id_professional", "procedures", ["id", "professional_id"]
    )

    status = postgresql.ENUM(
        "OPEN",
        "CONTACTED",
        "BOOKED",
        "DECLINED",
        "NO_RESPONSE",
        "DISMISSED",
        "CLOSED",
        name="return_opportunity_status",
        create_type=False,
    )
    status.create(op.get_bind(), checkfirst=True)

    contact_channel = postgresql.ENUM(
        "WHATSAPP",
        "PHONE",
        "IN_PERSON",
        "OTHER",
        name="contact_channel",
        create_type=False,
    )
    contact_channel.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "return_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procedure_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_sale_item_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("potential_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", status, nullable=False, server_default="OPEN"),
        sa.Column("contacted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("contact_channel", contact_channel, nullable=True),
        sa.Column(
            "resolved_by_sale_id", postgresql.UUID(as_uuid=True), nullable=True
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
        sa.ForeignKeyConstraint(
            ["patient_id", "professional_id"],
            ["patients.id", "patients.professional_id"],
            name="fk_return_opportunities_patient",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_id", "professional_id"],
            ["procedures.id", "procedures.professional_id"],
            name="fk_return_opportunities_procedure",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_sale_item_id", "professional_id"],
            ["sale_items.id", "sale_items.professional_id"],
            name="fk_return_opportunities_source_sale_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_return_opportunities_resolved_by_sale",
            ondelete="RESTRICT",
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
        "ix_return_opportunities_procedure_id",
        "return_opportunities",
        ["procedure_id"],
    )
    op.create_index(
        "ix_return_opportunities_source_sale_item_id",
        "return_opportunities",
        ["source_sale_item_id"],
    )
    # Query de listagem (§20.4): filtra/ordena por due_date dentro de um
    # tenant, geralmente excluindo status terminal.
    op.create_index(
        "ix_return_opportunities_professional_due_status",
        "return_opportunities",
        ["professional_id", "due_date", "status"],
    )
    # No máximo uma oportunidade ATIVA por item-fonte — histórico de
    # oportunidades fechadas (CLOSED) não compete com uma nova aberta
    # para o mesmo item (não deveria acontecer na prática, mas a
    # constraint documenta e garante a invariante).
    op.create_index(
        "uq_return_opportunities_source_sale_item_active",
        "return_opportunities",
        ["source_sale_item_id"],
        unique=True,
        postgresql_where=sa.text("status != 'CLOSED'"),
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

    # §20.4 — índice que faltava para a busca de "última sessão COMPLETED
    # de um item" (window.calculate_due_date) e para contagem por
    # período (já usado por count_completed_in_period).
    op.create_index(
        "ix_sessions_professional_completed_at",
        "sessions",
        ["professional_id", "completed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sessions_professional_completed_at", table_name="sessions")
    op.drop_table("return_opportunities")
    op.execute("DROP TYPE IF EXISTS contact_channel")
    op.execute("DROP TYPE IF EXISTS return_opportunity_status")
    op.drop_constraint(
        "uq_procedures_id_professional", "procedures", type_="unique"
    )
    op.drop_constraint("uq_patients_id_professional", "patients", type_="unique")
