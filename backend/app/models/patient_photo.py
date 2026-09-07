"""PatientPhoto — Registro e evolução fotográfica clínica do paciente (US-01).

Permite registrar fotos de Antes, Depois e Acompanhamento Geral vinculadas
ao paciente e opcionalmente a um procedimento específico.
Isolamento multitenant estrito via TenantModel.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel


class PhotoType(StrEnum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    GENERAL = "GENERAL"


class PatientPhoto(TenantModel):
    __tablename__ = "patient_photos"

    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    procedure_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("procedures.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    photo_type: Mapped[PhotoType] = mapped_column(
        Enum(PhotoType, name="patient_photo_type", native_enum=False),
        default=PhotoType.BEFORE,
        nullable=False,
    )
    # Suporta data URI base64 (data:image/...) ou URL pública/assinada
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    # LGPD: consentimento específico da paciente para publicação anônima em redes/portfólio
    authorized_social_media: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Relacionamentos opcionais para conveniência de navegação
    patient = relationship("Patient", backref="photos", foreign_keys=[patient_id])
    procedure = relationship("Procedure", foreign_keys=[procedure_id])
