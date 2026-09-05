"""platform_tables_rls: RLS em clinics, users, professionals e terms_acceptances (S-02a)

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-05

S-02a: Ativa ENABLE ROW LEVEL SECURITY + FORCE ROW LEVEL SECURITY nas tabelas de plataforma
com políticas baseadas em app.clinic_id, app.professional_id e app.bypass_tenant (para super-admin).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. clinics
    op.execute("ALTER TABLE clinics ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE clinics FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY clinic_isolation ON clinics
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR id = NULLIF(current_setting('app.clinic_id', true), '')::uuid
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR id = NULLIF(current_setting('app.clinic_id', true), '')::uuid
          );
        """
    )

    # 2. users
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY user_isolation ON users
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            OR (clinic_id IS NOT NULL AND clinic_id = NULLIF(current_setting('app.clinic_id', true), '')::uuid)
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            OR (clinic_id IS NOT NULL AND clinic_id = NULLIF(current_setting('app.clinic_id', true), '')::uuid)
          );
        """
    )

    # 3. professionals
    op.execute("ALTER TABLE professionals ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE professionals FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY professional_isolation ON professionals
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            OR (clinic_id IS NOT NULL AND clinic_id = NULLIF(current_setting('app.clinic_id', true), '')::uuid)
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR id = NULLIF(current_setting('app.professional_id', true), '')::uuid
            OR (clinic_id IS NOT NULL AND clinic_id = NULLIF(current_setting('app.clinic_id', true), '')::uuid)
          );
        """
    )

    # 4. terms_acceptances
    op.execute("ALTER TABLE terms_acceptances ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE terms_acceptances FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY terms_acceptance_isolation ON terms_acceptances
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR user_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR user_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS terms_acceptance_isolation ON terms_acceptances")
    op.execute("ALTER TABLE terms_acceptances NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE terms_acceptances DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS professional_isolation ON professionals")
    op.execute("ALTER TABLE professionals NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE professionals DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS user_isolation ON users")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS clinic_isolation ON clinics")
    op.execute("ALTER TABLE clinics NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE clinics DISABLE ROW LEVEL SECURITY")
