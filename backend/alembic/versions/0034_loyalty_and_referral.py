"""loyalty_and_referral: Clube VIP, pontuacao de fidelidade, indicacoes e transacoes

Revision ID: 0034
Revises: 0033
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Configurações de fidelidade em financial_settings
    op.add_column(
        "financial_settings",
        sa.Column("loyalty_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "financial_settings",
        sa.Column("loyalty_points_per_currency", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.10")),
    )
    op.add_column(
        "financial_settings",
        sa.Column("loyalty_redemption_rate", sa.Numeric(5, 2), nullable=False, server_default=sa.text("1.00")),
    )
    op.add_column(
        "financial_settings",
        sa.Column("referral_reward_points", sa.Integer(), nullable=False, server_default=sa.text("50")),
    )

    # 2. Campos de fidelidade e indicação em patients
    op.add_column(
        "patients",
        sa.Column("loyalty_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "patients",
        sa.Column("vip_tier", sa.String(20), nullable=False, server_default=sa.text("'BRONZE'")),
    )
    op.add_column(
        "patients",
        sa.Column("referral_code", sa.String(20), nullable=True),
    )
    op.add_column(
        "patients",
        sa.Column(
            "referred_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_patients_vip_tier", "patients", ["vip_tier"])
    op.create_index("ix_patients_referral_code", "patients", ["referral_code"])

    # 3. Tabela de transações / extrato de fidelidade (loyalty_transactions)
    op.create_table(
        "loyalty_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
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
            "sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("transaction_type", sa.String(20), nullable=False, server_default="EARNED"),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
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

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON loyalty_transactions TO estetica_app;
                END IF;
            END
            $$;
            """
        )
        op.execute("ALTER TABLE loyalty_transactions ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE loyalty_transactions FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON loyalty_transactions
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
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON loyalty_transactions")
    op.drop_table("loyalty_transactions")

    op.drop_index("ix_patients_referral_code", table_name="patients")
    op.drop_index("ix_patients_vip_tier", table_name="patients")
    op.drop_column("patients", "referred_by_id")
    op.drop_column("patients", "referral_code")
    op.drop_column("patients", "vip_tier")
    op.drop_column("patients", "loyalty_points")

    op.drop_column("financial_settings", "referral_reward_points")
    op.drop_column("financial_settings", "loyalty_redemption_rate")
    op.drop_column("financial_settings", "loyalty_points_per_currency")
    op.drop_column("financial_settings", "loyalty_enabled")
