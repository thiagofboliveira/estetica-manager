"""ReturnOpportunity — oportunidade de retorno gerada pelo motor de retenção (MVP v6 §14, TASK-025).

Timing (UPCOMING/DUE/OVERDUE) é derivado em runtime e nunca persistido.
Status (OPEN, CONTACTED, BOOKED, DECLINED, NO_RESPONSE, DISMISSED, CLOSED)
é persistido e evolui por eventos.

Oportunidade é resolvida (status=CLOSED) na nova VENDA (POST /sales), gravando
resolved_by_sale_id (TASK-028).
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.retention.enums import ContactChannel, ReturnOpportunityStatus
from app.models.base import TenantModel

__all__ = ["ReturnOpportunity", "ReturnOpportunityStatus", "ContactChannel"]


class ReturnOpportunity(TenantModel):
    __tablename__ = "return_opportunities"

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    procedure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("procedures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_sale_item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sale_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[ReturnOpportunityStatus] = mapped_column(
        Enum(
            ReturnOpportunityStatus,
            name="return_opportunity_status",
            native_enum=False,
        ),
        nullable=False,
        default=ReturnOpportunityStatus.OPEN,
        index=True,
    )
    contacted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    contact_channel: Mapped[ContactChannel | None] = mapped_column(
        Enum(ContactChannel, name="contact_channel", native_enum=False),
        nullable=True,
    )
    contact_status: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_by_sale_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    patient = relationship("Patient", lazy="joined")
    procedure = relationship("Procedure", lazy="joined")
