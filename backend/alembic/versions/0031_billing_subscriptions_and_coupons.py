"""billing_subscriptions_and_coupons: Modelagem de assinaturas, controle de trial 14 dias e cupons de desconto

Revision ID: 0031
Revises: 0030
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tabela coupons
    op.create_table(
        "coupons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("valid_from", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("times_redeemed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("allowed_cycles", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. Tabela subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("plan_id", sa.String(50), nullable=False, server_default="pro"),
        sa.Column("cycle", sa.String(20), nullable=False, server_default="MONTHLY"),
        sa.Column("status", sa.String(30), nullable=False, server_default="TRIALING"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="80.00"),
        sa.Column("trial_started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "trial_ends_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now() + interval '14 days'"),
        ),
        sa.Column("current_period_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("asaas_customer_id", sa.String(100), nullable=True, index=True),
        sa.Column("asaas_subscription_id", sa.String(100), nullable=True, index=True),
        sa.Column(
            "coupon_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("coupons.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("payment_method", sa.String(30), nullable=True),
        sa.Column("invoice_url", sa.String(500), nullable=True),
        sa.Column("pix_qrcode_payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 3. Grants e RLS
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON coupons TO estetica_app;
                    GRANT SELECT, INSERT, UPDATE, DELETE ON subscriptions TO estetica_app;
                END IF;
            END
            $$;
            """
        )

        # RLS em subscriptions (por clinic_id)
        op.execute("ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY subscription_isolation ON subscriptions
              FOR ALL TO estetica_app
              USING (
                current_setting('app.bypass_tenant', true) = 'true'
                OR (clinic_id IS NOT NULL AND clinic_id = NULLIF(current_setting('app.clinic_id', true), '')::uuid)
              )
              WITH CHECK (
                current_setting('app.bypass_tenant', true) = 'true'
                OR (clinic_id IS NOT NULL AND clinic_id = NULLIF(current_setting('app.clinic_id', true), '')::uuid)
              );
            """
        )

        # RLS em coupons (todos podem ler para validar, escrita só bypass_tenant)
        op.execute("ALTER TABLE coupons ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE coupons FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY coupon_tenant_isolation ON coupons
              FOR ALL TO estetica_app
              USING (
                current_setting('app.bypass_tenant', true) = 'true'
                OR is_active = true
              )
              WITH CHECK (
                current_setting('app.bypass_tenant', true) = 'true'
              );
            """
        )

        # 4. Seeds de cupons iniciais de inauguração
        op.execute(
            """
            INSERT INTO coupons (id, code, discount_type, discount_value, is_active, max_redemptions, allowed_cycles)
            VALUES
              (gen_random_uuid(), 'INAUGURACAO', 'PERCENTAGE', 10.00, true, 100, NULL),
              (gen_random_uuid(), 'PRIMEIRAS10', 'FIXED', 30.00, true, 10, NULL)
            ON CONFLICT (code) DO NOTHING;
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS coupon_tenant_isolation ON coupons")
        op.execute("DROP POLICY IF EXISTS subscription_isolation ON subscriptions")

    op.drop_table("subscriptions")
    op.drop_table("coupons")
