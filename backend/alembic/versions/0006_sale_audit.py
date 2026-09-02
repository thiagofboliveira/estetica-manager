"""sale_audit + RLS

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-02

⚠️ Gerada manualmente (sem acesso de rede a Postgres neste ambiente de
dev). Revisar contra app/models/sale_audit.py antes de aplicar.

Cobre T-017 (MVP v6 §27, A-02). sales já tem UniqueConstraint(id,
professional_id) desde 0001/0002 (uq_sales_id_professional) — sale_audit
referencia essa constraint diretamente via FK composta, sem precisar
adicioná-la de novo.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sale_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("original_sale_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "replacement_sale_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("corrected_at", sa.TIMESTAMP(timezone=True), nullable=False),
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
            ["original_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_sale_audit_original_sale",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["replacement_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_sale_audit_replacement_sale",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_sale_audit_professional_id", "sale_audit", ["professional_id"]
    )
    op.create_index(
        "ix_sale_audit_original_sale_id", "sale_audit", ["original_sale_id"]
    )
    op.create_index(
        "ix_sale_audit_replacement_sale_id", "sale_audit", ["replacement_sale_id"]
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON sale_audit TO estetica_app")
    op.execute("ALTER TABLE sale_audit ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sale_audit FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON sale_audit
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.drop_table("sale_audit")
