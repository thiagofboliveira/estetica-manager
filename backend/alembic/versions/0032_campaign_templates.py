"""campaign_templates: Modelos configuraveis de campanhas e disparos WhatsApp

Revision ID: 0032
Revises: 0031
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaign_templates",
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
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="promos"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
    op.create_index("ix_campaign_templates_category", "campaign_templates", ["category"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON campaign_templates TO estetica_app;
                END IF;
            END
            $$;
            """
        )
        op.execute("ALTER TABLE campaign_templates ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE campaign_templates FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON campaign_templates
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
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON campaign_templates")
    op.drop_index("ix_campaign_templates_category", table_name="campaign_templates")
    op.drop_table("campaign_templates")
