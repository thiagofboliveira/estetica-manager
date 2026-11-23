"""create_ai_usage: contador mensal de textos gerados por IA (teto de custo)

Revision ID: 0038
Revises: 0037
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("period_month", sa.Date(), nullable=False),
        sa.Column("drafts_count", sa.Integer(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("professional_id", "period_month", name="uq_ai_usage_month"),
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON ai_usage TO estetica_app;
                END IF;
            END
            $$;
            """
        )
        op.execute("ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE ai_usage FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON ai_usage
                FOR ALL
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
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON ai_usage")
    op.drop_table("ai_usage")
