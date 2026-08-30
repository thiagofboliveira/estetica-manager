"""Booking — agendamento provisório / reserva de horário sem venda prévia (MVP v7.1 §16.6, TASK-034a).

Não possui campos financeiros (preço, desconto).
Ao criar a venda (POST /sales), pode ser convertido atomicamente passando booking_id.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.bookings.enums import BookingStatus
from app.models.base import TenantModel
from app.models.procedure import Modality

__all__ = ["Booking", "BookingStatus"]


class Booking(TenantModel):
    __tablename__ = "bookings"

    patient_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    patient_name_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
    modality: Mapped[Modality] = mapped_column(
        Enum(Modality, name="modality", native_enum=False),
        nullable=False,
        default=Modality.IN_PERSON,
    )
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status", native_enum=False),
        nullable=False,
        default=BookingStatus.SCHEDULED,
        index=True,
    )
    sale_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    patient = relationship("Patient", lazy="joined")
