"""booking_unique_slot: impede duplo agendamento no mesmo horario

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Cancela bookings duplicados pré-existentes mantendo apenas o mais antigo ativo (A-04)
    op.execute(
        """
        UPDATE bookings
        SET status = 'CANCELLED'
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY professional_id, scheduled_at 
                    ORDER BY created_at ASC, id ASC
                ) as rnum
                FROM bookings
                WHERE status = 'SCHEDULED'
            ) t
            WHERE t.rnum > 1
        );
        """
    )

    # 2. Cria indice unico condicional para impedir agendamentos simultaneos ativos (A-04)
    op.create_index(
        "uq_bookings_active_slot",
        "bookings",
        ["professional_id", "scheduled_at"],
        unique=True,
        postgresql_where=sa.text("status = 'SCHEDULED'"),
    )


def downgrade() -> None:
    op.drop_index("uq_bookings_active_slot", table_name="bookings")
