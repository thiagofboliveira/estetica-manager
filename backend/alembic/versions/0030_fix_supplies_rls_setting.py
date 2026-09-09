"""fix: corrige setting de RLS nas tabelas de estoque e insumos

As migrations 0028 e 0029 criaram as policies de Row-Level Security
referenciando `app.current_professional_id`, mas o backend define
`app.professional_id` em todas as conexões transacionais (app/db/session.py).

Como o setting nunca era populado, a RLS avaliava como NULL e bloqueava
qualquer INSERT/UPDATE/SELECT nas três tabelas afetadas.

Revision ID: 0030
Revises: 0029
Create Date: 2026-09-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        ALTER POLICY tenant_isolation ON supplies
            USING (
                professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            )
            WITH CHECK (
                professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            )
        """
    )

    op.execute(
        """
        ALTER POLICY tenant_isolation ON supply_movements
            USING (
                professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            )
            WITH CHECK (
                professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            )
        """
    )

    op.execute(
        """
        ALTER POLICY tenant_isolation ON procedure_supplies
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
    if bind.dialect.name != "postgresql":
        return

    # Reverte para o estado original quebrado (apenas para completude do downgrade)
    op.execute(
        """
        ALTER POLICY tenant_isolation ON supplies
            USING (
                professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
            )
            WITH CHECK (
                professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
            )
        """
    )

    op.execute(
        """
        ALTER POLICY tenant_isolation ON supply_movements
            USING (
                professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
            )
            WITH CHECK (
                professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
            )
        """
    )

    op.execute(
        """
        ALTER POLICY tenant_isolation ON procedure_supplies
            USING (
                professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
            )
            WITH CHECK (
                professional_id = NULLIF(current_setting('app.current_professional_id', true), '')::uuid
            )
        """
    )
