"""despesas fixas: fixed_expenses + RLS

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-29

⚠️ Gerada manualmente, seguindo o padrão de 0001_fundacao.py/0002_financeiro.py
(sem acesso de rede a Postgres neste ambiente de dev para autogenerate).
Revisar contra app/models/fixed_expense.py antes de aplicar em banco novo.

Cobre T-021a (fixed_expenses). MVP v7.1 §12.5, pós-entrevista com a
cliente zero: ela não tem split percentual de clínica, paga aluguel
fixo de sala — categoria ortogonal ao motor de lucro por venda.

Reproduz o esqueleto de _create_simple_tenant_table de 0002_financeiro.py
(sem FK composta contra outra tabela de tenant — fixed_expenses não tem
tabela pai além de professionals).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_simple_tenant_table(name: str, extra_columns: list[sa.Column]) -> None:
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
    periodicity = postgresql.ENUM(
        "MONTHLY", "YEARLY", name="expense_periodicity", create_type=False
    )
    periodicity.create(op.get_bind(), checkfirst=True)

    _create_simple_tenant_table(
        "fixed_expenses",
        [
            sa.Column("label", sa.String(), nullable=False),
            # Texto livre de propósito — sem categoria fechada no MVP
            # (só um caso real, aluguel, existia na entrevista).
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column(
                "periodicity", periodicity, nullable=False, server_default="MONTHLY"
            ),
            sa.Column("active_from", sa.Date(), nullable=False),
            # NULL = ainda vigente. "Excluir" fecha active_to=hoje.
            sa.Column("active_to", sa.Date(), nullable=True),
        ],
    )
    op.create_check_constraint(
        "ck_fixed_expenses_vigencia_coerente",
        "fixed_expenses",
        "active_to IS NULL OR active_to >= active_from",
    )


def downgrade() -> None:
    op.drop_table("fixed_expenses")
    op.execute("DROP TYPE IF EXISTS expense_periodicity")
