"""terms_acceptances: auditoria de aceite de termos e política de privacidade LGPD (G-10)

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-05

G-10: Política de Privacidade e Termos de Uso publicados + aceite formal registrado
pela Controladora (profissional/usuária) com timestamp e versão auditáveis.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Colunas de conveniência em users para verificação rápida de status de aceite
    op.add_column(
        "users",
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("terms_version", sa.String(length=32), nullable=True),
    )

    # 2. Tabela append-only de auditoria de aceite de termos (LGPD)
    op.create_table(
        "terms_acceptances",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("terms_version", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_terms_acceptances_user_id",
        "terms_acceptances",
        ["user_id"],
    )

    # Privilégios para o role da aplicação
    op.execute("GRANT SELECT, INSERT ON TABLE terms_acceptances TO estetica_app;")


def downgrade() -> None:
    op.execute("REVOKE ALL ON TABLE terms_acceptances FROM estetica_app;")
    op.drop_index("ix_terms_acceptances_user_id", table_name="terms_acceptances")
    op.drop_table("terms_acceptances")
    op.drop_column("users", "terms_version")
    op.drop_column("users", "terms_accepted_at")
