"""supplies_and_inventory: Gestão genérica de insumos, estoque fechado e movimentações

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. supplies
    op.create_table(
        "supplies",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="CONSUMABLE"),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("unit_measure", sa.String(30), nullable=False, server_default="UN"),
        sa.Column("current_stock", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("min_stock_alert", sa.Numeric(10, 2), nullable=True),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
    op.create_index("ix_supplies_name", "supplies", ["name"])
    op.create_index("ix_supplies_category", "supplies", ["category"])

    # 2. supply_movements
    op.create_table(
        "supply_movements",
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
            "supply_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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

    # 3. add supply_id column to open_vials
    op.add_column(
        "open_vials",
        sa.Column(
            "supply_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_open_vials_supply_id", "open_vials", ["supply_id"])

    # 4. Grants & RLS
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON supplies TO estetica_app;
                    GRANT SELECT, INSERT, UPDATE, DELETE ON supply_movements TO estetica_app;
                END IF;
            END
            $$;
            """
        )
        op.execute("ALTER TABLE supplies ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE supplies FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON supplies
                FOR ALL
                USING (
                    professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
                )
                WITH CHECK (
                    professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
                )
            """
        )

        op.execute("ALTER TABLE supply_movements ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE supply_movements FORCE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation ON supply_movements
                FOR ALL
                USING (
                    professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
                )
                WITH CHECK (
                    professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
                )
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON supply_movements")
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON supplies")

    op.drop_index("ix_open_vials_supply_id", table_name="open_vials")
    op.drop_column("open_vials", "supply_id")
    op.drop_table("supply_movements")
    op.drop_index("ix_supplies_category", table_name="supplies")
    op.drop_index("ix_supplies_name", table_name="supplies")
    op.drop_table("supplies")
