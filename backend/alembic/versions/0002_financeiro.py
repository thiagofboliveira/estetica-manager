"""financeiro: financial_settings, payment_fee_rules, sales, sale_items,
sessions + procedures.default_modality + RLS

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29

⚠️ Gerada manualmente, seguindo o padrão de 0001_fundacao.py — mesmo
motivo (sem acesso de rede a Postgres neste ambiente de dev para
autogenerate). Revisar contra app/models/ antes de aplicar em banco novo.

Cobre T-007 (financial_settings), T-008 (payment_fee_rules), T-009a
(procedures.default_modality — de passagem, documentado no BACKLOG.md:
é barato e senão sessions.modality não teria de onde copiar), T-012
(sales), T-013 (sale_items), T-014 (sessions).

Decisão de design documentada (ver BACKLOG.md): FK composta
(id, professional_id) em sales -> sale_items -> sessions, seguindo
backend/ENGENHARIA.md §1 "Denormalizar professional_id nas filhas" —
evita subquery na policy de RLS.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_tenant_table_with_composite_parent(
    name: str,
    extra_columns: list[sa.Column],
    parent_table: str,
    parent_fk_column: str,
    fk_name: str,
) -> None:
    """Variante de create_tenant_table (0001) para tabelas filhas que
    referenciam outra tabela de tenant via FK COMPOSTA
    (parent_fk_column, professional_id) -> (parent_table.id,
    parent_table.professional_id). Isso garante que a linha filha nunca
    aponta para um pai de OUTRO tenant, mesmo com bug de aplicação
    (backend/ENGENHARIA.md §1)."""
    op.create_table(
        name,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *extra_columns,
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
            [parent_fk_column, "professional_id"],
            [f"{parent_table}.id", f"{parent_table}.professional_id"],
            name=fk_name,
            ondelete="RESTRICT",
        ),
    )
    op.create_index(f"ix_{name}_professional_id", name, ["professional_id"])
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {name} TO estetica_app")
    op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {name}
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )


def _create_simple_tenant_table(name: str, extra_columns: list[sa.Column]) -> None:
    """Mesmo esqueleto de create_tenant_table em 0001, reproduzido aqui
    (sem o helper daquele módulo estar acessível diretamente) para
    tabelas sem FK composta contra outra tabela de tenant."""
    op.create_table(
        name,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *extra_columns,
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
    op.create_index(f"ix_{name}_professional_id", name, ["professional_id"])
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {name} TO estetica_app")
    op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {name}
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tipos compartilhados
    # ------------------------------------------------------------------
    modality = postgresql.ENUM(
        "IN_PERSON", "REMOTE", name="modality", create_type=False
    )
    modality.create(op.get_bind(), checkfirst=True)

    split_base = postgresql.ENUM(
        "GROSS", "NET_OF_FEE", name="split_base", create_type=False
    )
    split_base.create(op.get_bind(), checkfirst=True)

    fee_payer = postgresql.ENUM(
        "PROFESSIONAL", "CLINIC", "SPLIT_PRO_RATA", name="fee_payer", create_type=False
    )
    fee_payer.create(op.get_bind(), checkfirst=True)

    payment_method = postgresql.ENUM(
        "PIX",
        "DEBIT",
        "CREDIT",
        "CASH",
        "TRANSFER",
        name="payment_method",
        create_type=False,
    )
    payment_method.create(op.get_bind(), checkfirst=True)

    sale_type = postgresql.ENUM(
        "SINGLE", "PACKAGE", name="sale_type", create_type=False
    )
    sale_type.create(op.get_bind(), checkfirst=True)

    sale_status = postgresql.ENUM(
        "ACTIVE", "REFUNDED", name="sale_status", create_type=False
    )
    sale_status.create(op.get_bind(), checkfirst=True)

    session_status = postgresql.ENUM(
        "PENDING",
        "SCHEDULED",
        "CONFIRMED",
        "COMPLETED",
        "CANCELLED",
        "NO_SHOW",
        "EXPIRED",
        name="session_status",
        create_type=False,
    )
    session_status.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # T-009a — procedures.default_modality (de passagem: barato e sem
    # ele sessions.modality não teria de onde copiar na criação).
    # ------------------------------------------------------------------
    op.add_column(
        "procedures",
        sa.Column(
            "default_modality",
            modality,
            nullable=False,
            server_default="IN_PERSON",
        ),
    )

    # ------------------------------------------------------------------
    # T-007 — financial_settings (singleton por tenant).
    # ------------------------------------------------------------------
    _create_simple_tenant_table(
        "financial_settings",
        [
            sa.Column(
                "split_clinic_percentage",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0.00",
            ),
            sa.Column("split_base", split_base, nullable=False, server_default="GROSS"),
            sa.Column(
                "fee_payer", fee_payer, nullable=False, server_default="PROFESSIONAL"
            ),
            sa.Column(
                "pix_fee_percentage",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0.00",
            ),
            sa.Column(
                "debit_card_fee_percentage",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="1.99",
            ),
            sa.Column(
                "default_payment_method",
                payment_method,
                nullable=False,
                server_default="PIX",
            ),
        ],
    )
    op.create_unique_constraint(
        "uq_financial_settings_professional", "financial_settings", ["professional_id"]
    )

    # ------------------------------------------------------------------
    # T-008 — payment_fee_rules (faixas por parcela).
    # ------------------------------------------------------------------
    _create_simple_tenant_table(
        "payment_fee_rules",
        [
            sa.Column("payment_method", payment_method, nullable=False),
            sa.Column(
                "installments_min", sa.Integer(), nullable=False, server_default="1"
            ),
            sa.Column(
                "installments_max", sa.Integer(), nullable=False, server_default="1"
            ),
            sa.Column(
                "fee_percentage",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0.00",
            ),
            sa.Column(
                "fixed_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"
            ),
        ],
    )
    op.create_check_constraint(
        "ck_payment_fee_rules_min_le_max",
        "payment_fee_rules",
        "installments_min <= installments_max",
    )

    # ------------------------------------------------------------------
    # T-012 — sales. Snapshot congelado (invariante I3): split_applied,
    # split_base_applied, fee_payer_applied, fee_applied,
    # fee_amount_applied NUNCA relidos de financial_settings depois de
    # criados.
    # ------------------------------------------------------------------
    _create_simple_tenant_table(
        "sales",
        [
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("type", sale_type, nullable=False),
            sa.Column("sold_at", sa.Date(), nullable=False),
            sa.Column("status", sale_status, nullable=False, server_default="ACTIVE"),
            sa.Column("payment_method", payment_method, nullable=False),
            sa.Column("installments", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("items_total", sa.Numeric(12, 2), nullable=False),
            sa.Column(
                "discount_amount",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0.00",
            ),
            sa.Column("gross_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("split_applied", sa.Numeric(5, 2), nullable=False),
            sa.Column("split_base_applied", split_base, nullable=False),
            sa.Column("fee_payer_applied", fee_payer, nullable=False),
            sa.Column("fee_applied", sa.Numeric(5, 2), nullable=False),
            sa.Column("fee_amount_applied", sa.Numeric(12, 2), nullable=False),
            sa.Column("cost_provisioned", sa.Numeric(12, 2), nullable=False),
            sa.Column("cost_realized", sa.Numeric(12, 2), nullable=False),
            sa.Column("net_profit", sa.Numeric(12, 2), nullable=False),
            sa.Column("margin", sa.Numeric(5, 4), nullable=True),
            sa.Column("expected_receipt_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column(
                "snapshot_payload",
                postgresql.JSONB(),
                nullable=False,
                server_default="{}",
            ),
            sa.Column("idempotency_key", sa.String(), nullable=True),
            sa.Column("idempotency_body_hash", sa.String(), nullable=True),
        ],
    )
    op.create_index("ix_sales_patient_id", "sales", ["patient_id"])
    op.create_index(
        "ix_sales_prof_created",
        "sales",
        ["professional_id", sa.text("created_at DESC")],
    )
    op.create_unique_constraint(
        "uq_sales_id_professional", "sales", ["id", "professional_id"]
    )
    op.create_check_constraint(
        "ck_sales_gross_coerente",
        "sales",
        "gross_amount = items_total - discount_amount",
    )
    # Idempotência (T-015a): mesma chave só pode resolver para 1 venda
    # por tenant. Parcial (WHERE NOT NULL) — vendas sem chave (nenhuma
    # enviada) não competem entre si.
    op.create_index(
        "uq_sales_idempotency_key",
        "sales",
        ["professional_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # ------------------------------------------------------------------
    # T-013 — sale_items. FK composta contra (sales.id, professional_id).
    # ------------------------------------------------------------------
    _create_tenant_table_with_composite_parent(
        "sale_items",
        [
            sa.Column("sale_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "procedure_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("procedures.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("unit_cost_estimated", sa.Numeric(12, 2), nullable=False),
            sa.Column("return_interval_applied", sa.Integer(), nullable=True),
            sa.Column(
                "discount_allocated",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0.00",
            ),
        ],
        parent_table="sales",
        parent_fk_column="sale_id",
        fk_name="fk_sale_items_sale",
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])
    # Necessário para sessions referenciar (sale_item_id, professional_id)
    # via FK composta — mesmo padrão de uq_sales_id_professional.
    op.create_unique_constraint(
        "uq_sale_items_id_professional", "sale_items", ["id", "professional_id"]
    )

    # ------------------------------------------------------------------
    # T-014 — sessions. professional_id desnormalizado (já coberto pelo
    # esqueleto padrão); FK composta contra (sale_items.id,
    # professional_id). modality NOT NULL, copiada na criação (v7.1).
    # ------------------------------------------------------------------
    _create_tenant_table_with_composite_parent(
        "sessions",
        [
            sa.Column("sale_item_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("sequence_number", sa.Integer(), nullable=False),
            sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column("status", session_status, nullable=False),
            sa.Column("modality", modality, nullable=False),
            sa.Column("cost_override", sa.Numeric(12, 2), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
        ],
        parent_table="sale_items",
        parent_fk_column="sale_item_id",
        fk_name="fk_sessions_sale_item",
    )
    op.create_index("ix_sessions_sale_item_id", "sessions", ["sale_item_id"])


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("sale_items")
    op.drop_table("sales")
    op.drop_table("payment_fee_rules")
    op.drop_table("financial_settings")
    op.drop_column("procedures", "default_modality")

    op.execute("DROP TYPE IF EXISTS session_status")
    op.execute("DROP TYPE IF EXISTS sale_status")
    op.execute("DROP TYPE IF EXISTS sale_type")
    op.execute("DROP TYPE IF EXISTS payment_method")
    op.execute("DROP TYPE IF EXISTS fee_payer")
    op.execute("DROP TYPE IF EXISTS split_base")
    op.execute("DROP TYPE IF EXISTS modality")
