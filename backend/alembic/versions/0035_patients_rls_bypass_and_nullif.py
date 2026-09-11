"""patients_rls_bypass_and_nullif: Permite bypass_tenant e NULLIF na policy de patients para Cartão VIP público

Revision ID: 0035
Revises: 0034
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON patients")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON patients
          FOR ALL TO estetica_app
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
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON patients")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON patients
          FOR ALL TO estetica_app
          USING (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid);
        """
    )
