"""fundacao: users, professionals, patients, procedures + RLS

Revision ID: 0001
Revises:
Create Date: 2026-08-29

⚠️ Gerada manualmente, não por autogenerate — este ambiente de dev não
tem acesso de rede a um Postgres para rodar `alembic revision
--autogenerate`. Revisar o DDL abaixo contra os modelos SQLAlchemy
(app/models/) antes de aplicar em qualquer banco real, e depois rodar
`alembic check` num ambiente com banco disponível.

Inclui a role de aplicação e as policies de RLS (T-057a, T-058) — o
autogenerate do SQLAlchemy nunca geraria isso sozinho, pois RLS não é
modelado pelo ORM.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Role de aplicação — NOBYPASSRLS (T-057a).
    # Se a app conectar como owner ou service_role, RLS é ignorado
    # silenciosamente: as policies existem, os testes passam, a proteção
    # é zero. A DATABASE_URL da app usa esta role; migrations usam o
    # owner (DATABASE_URL_MIGRATIONS).
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'estetica_app') THEN
                CREATE ROLE estetica_app LOGIN NOBYPASSRLS;
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO estetica_app")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO estetica_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO estetica_app"
    )

    # Extensão para busca de paciente sem sensibilidade a acento
    # (repositories/patient.py usa func.unaccent).
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # ------------------------------------------------------------------
    # users — espelho de auth.users do Supabase. Sem password_hash: a
    # fonte de verdade de identidade é o Supabase Auth.
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON users TO estetica_app")

    # ------------------------------------------------------------------
    # professionals — o TENANT. Toda tabela de negócio referencia esta.
    # ------------------------------------------------------------------
    op.create_table(
        "professionals",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column(
            "timezone",
            sa.String(),
            nullable=False,
            server_default="America/Sao_Paulo",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON professionals TO estetica_app")

    def create_tenant_table(name: str, extra_columns: list[sa.Column]) -> None:
        """Toda tabela de tenant tem o mesmo esqueleto: id, professional_id
        (FK RESTRICT), created_at, updated_at, RLS habilitado e forçado,
        policy com USING e WITH CHECK, e índice liderando por
        professional_id (a policy vira predicado em toda query)."""
        op.create_table(
            name,
            sa.Column(
                "id", postgresql.UUID(as_uuid=True), primary_key=True
            ),
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

    # ------------------------------------------------------------------
    # patients — dado sensível (LGPD Art. 5º, II).
    # ------------------------------------------------------------------
    create_tenant_table(
        "patients",
        [
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("birth_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "consent_whatsapp",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
            sa.Column(
                "consent_at", sa.TIMESTAMP(timezone=True), nullable=True
            ),
            sa.Column(
                "opted_out_at", sa.TIMESTAMP(timezone=True), nullable=True
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "anonymized_at", sa.TIMESTAMP(timezone=True), nullable=True
            ),
        ],
    )
    op.create_index("ix_patients_phone", "patients", ["phone"])

    # ------------------------------------------------------------------
    # procedures — price/estimated_cost são DEFAULTS de UI, não fonte de
    # verdade: o valor aplicado numa venda é congelado no snapshot.
    # ------------------------------------------------------------------
    procedure_type = postgresql.ENUM(
        "SERVICE", "PRODUCT", name="procedure_type", create_type=False
    )
    procedure_type.create(op.get_bind(), checkfirst=True)

    create_tenant_table(
        "procedures",
        [
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "type",
                procedure_type,
                nullable=False,
                server_default="SERVICE",
            ),
            sa.Column("price", sa.Numeric(12, 2), nullable=False),
            sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=False),
            sa.Column("return_interval_days", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        ],
    )


def downgrade() -> None:
    op.drop_table("procedures")
    op.execute("DROP TYPE IF EXISTS procedure_type")
    op.drop_table("patients")
    op.drop_table("professionals")
    op.drop_table("users")
    op.execute("DROP ROLE IF EXISTS estetica_app")
