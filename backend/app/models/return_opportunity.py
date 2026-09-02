"""ReturnOpportunity — motor de retorno (MVP v7.1 §11.6, §14, TASK-025).

Nasce quando um sale_item se ESGOTA (nenhuma sessão PENDING/SCHEDULED/
CONFIRMED restante e ao menos uma COMPLETED) — não a cada sessão. Um
pacote de 10 limpezas gera UMA oportunidade, não dez (ver
RetentionService.check_and_create_opportunity).

potential_value é congelado de (sale_item.unit_price * quantity) na
criação — mesma disciplina de snapshot de sales/sale_items (invariante
I3): não muda se o preço do procedimento mudar depois.

Duas dimensões independentes:
  - status: persistido, movido por evento (ver
    app.domain.retention.return_opportunity_state_machine).
  - timing (UPCOMING/DUE/OVERDUE): NUNCA persistido, calculado em toda
    leitura a partir de due_date vs hoje (ver
    app.domain.retention.window) — por isso não há coluna aqui.

resolved_by_sale_id é preenchido pelo fechamento automático na venda
(T-028, RetentionService.close_open_opportunities) — nunca por edição
manual. Índice parcial garante no máximo uma oportunidade ATIVA (status
!= CLOSED) por source_sale_item_id, preservando histórico de
oportunidades fechadas.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, ForeignKeyConstraint, Numeric
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
)
from app.models.base import TenantModel

__all__ = ["ReturnOpportunity", "ReturnOpportunityStatus", "ContactChannel"]


class ContactChannel(StrEnum):
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    IN_PERSON = "IN_PERSON"
    OTHER = "OTHER"


class ReturnOpportunity(TenantModel):
    __tablename__ = "return_opportunities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["patient_id", "professional_id"],
            ["patients.id", "patients.professional_id"],
            name="fk_return_opportunities_patient",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["procedure_id", "professional_id"],
            ["procedures.id", "procedures.professional_id"],
            name="fk_return_opportunities_procedure",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_sale_item_id", "professional_id"],
            ["sale_items.id", "sale_items.professional_id"],
            name="fk_return_opportunities_source_sale_item",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["resolved_by_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_return_opportunities_resolved_by_sale",
            ondelete="RESTRICT",
        ),
    )

    patient_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    procedure_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    source_sale_item_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    due_date: Mapped[date] = mapped_column(nullable=False)
    potential_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), nullable=False
    )
    status: Mapped[ReturnOpportunityStatus] = mapped_column(
        Enum(
            ReturnOpportunityStatus,
            name="return_opportunity_status",
            native_enum=False,
        ),
        nullable=False,
        default=ReturnOpportunityStatus.OPEN,
    )
    contacted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    contact_channel: Mapped[ContactChannel | None] = mapped_column(
        Enum(ContactChannel, name="contact_channel", native_enum=False),
        nullable=True,
    )
    resolved_by_sale_id: Mapped[PGUUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
