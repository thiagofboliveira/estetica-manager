"""create_loyalty_rewards: Tabela de catálogo de prêmios e recompensas por pontos de fidelidade

Revision ID: 0036
Revises: 0035
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "loyalty_rewards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("points_cost", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
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
    op.create_index("ix_loyalty_rewards_is_active", "loyalty_rewards", ["is_active"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON loyalty_rewards TO estetica_app;
                END IF;
            END
            $$;
            """
        )
        op.execute("ALTER TABLE loyalty_rewards ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE loyalty_rewards FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON loyalty_rewards
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
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON loyalty_rewards")
    op.drop_index("ix_loyalty_rewards_is_active", table_name="loyalty_rewards")
    op.drop_table("loyalty_rewards")
