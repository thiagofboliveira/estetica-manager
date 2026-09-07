"""anamnesis_tcle_and_signature: Termo de consentimento pós-procedimento e assinatura digital (US-02)

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. anamnesis_templates: adiciona tcle_content para customização dos cuidados pós-procedimento
    op.add_column(
        "anamnesis_templates",
        sa.Column("tcle_content", sa.Text(), nullable=True),
    )

    # 2. anamnesis_submissions: suporte a TCLE, carimbo de aceite, IP e assinatura desenhada
    op.add_column(
        "anamnesis_submissions",
        sa.Column(
            "tcle_accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "anamnesis_submissions",
        sa.Column("tcle_accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "anamnesis_submissions",
        sa.Column("signature_image", sa.Text(), nullable=True),
    )
    op.add_column(
        "anamnesis_submissions",
        sa.Column("client_ip", sa.String(45), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("anamnesis_submissions", "client_ip")
    op.drop_column("anamnesis_submissions", "signature_image")
    op.drop_column("anamnesis_submissions", "tcle_accepted_at")
    op.drop_column("anamnesis_submissions", "tcle_accepted")
    op.drop_column("anamnesis_templates", "tcle_content")
