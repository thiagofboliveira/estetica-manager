"""Session — a unidade de SERVIÇO (MVP v6 §11.3/§11.4, TASK-014).

Sessão NÃO TEM VALOR FINANCEIRO PRÓPRIO (invariante I5). Todo dinheiro
vive na Sale. Se sentir vontade de por `price` aqui, o modelo está sendo
violado — cost_override existe para AJUSTAR o custo (E5, insumo varia
por paciente), não para precificar a sessão.

professional_id é desnormalizado (copiado de Sale na criação) para que a
policy de RLS não precise de JOIN até sales — custo de uma coluna,
benefício de isolamento simples e rápido (backend/ENGENHARIA.md §1).

modality é NOT NULL, copiada de procedure.default_modality NA CRIAÇÃO —
nunca resolvida por COALESCE na leitura (ver nota em models/procedure.py
e MVP v7.1 §11.3).

Máquina de estados (§11.4) — ver
app/domain/sales/session_state_machine.py para as transições válidas.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, ForeignKeyConstraint, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.sales.session_state_machine import SessionStatus
from app.models.base import TenantModel
from app.models.procedure import Modality

# Re-exportado para quem importa de app.models.session (compatibilidade)
# — a definição canônica vive em domain/, que não pode importar daqui.
__all__ = ["Session", "SessionStatus"]


class Session(TenantModel):
    __tablename__ = "sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["sale_item_id", "professional_id"],
            ["sale_items.id", "sale_items.professional_id"],
            name="fk_sessions_sale_item",
            ondelete="RESTRICT",
        ),
    )

    sale_item_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    scheduled_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status", native_enum=False),
        nullable=False,
    )
    modality: Mapped[Modality] = mapped_column(
        Enum(Modality, name="modality", native_enum=False), nullable=False
    )
    cost_override: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2, asdecimal=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
