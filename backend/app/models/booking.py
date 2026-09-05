"""Booking — agendamento provisório / reserva de horário sem venda prévia (MVP v7.1 §16.6, TASK-034a).

Não possui campos financeiros (preço, desconto).
Ao criar a venda (POST /sales), pode ser convertido atomicamente passando booking_id.
"""

import secrets
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


def _generate_management_token() -> str:
    return secrets.token_urlsafe(32)


class Booking(TenantModel):
    __tablename__ = "bookings"

    patient_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    patient_name_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    procedure_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("procedures.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
    management_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        default=_generate_management_token,
    )
    sale_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    patient = relationship("Patient", lazy="joined")
    procedure = relationship("Procedure", lazy="joined")
