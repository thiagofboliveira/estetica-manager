"""Anamnese digital: templates, perguntas e submissões (AN-02).

Invariantes:
- I1: RLS por professional_id (TenantModel)
- I2: isolamento estrito de tenant
- I4: auditoria com timestamps automáticos
"""

import secrets
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel

__all__ = [
    "QuestionFieldType",
    "AnamnesisTemplate",
    "AnamnesisQuestion",
    "AnamnesisSubmission",
]


class QuestionFieldType(StrEnum):
    YES_NO = "yes_no"
    TEXT = "text"
    LONG_TEXT = "long_text"
    SELECT = "select"


def _generate_public_token() -> str:
    return secrets.token_urlsafe(32)


class AnamnesisTemplate(TenantModel):
    __tablename__ = "anamnesis_templates"

    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Ficha de Anamnese Facial e Corporal",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tcle_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_request_on_booking: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    questions: Mapped[list["AnamnesisQuestion"]] = relationship(
        "AnamnesisQuestion",
        back_populates="template",
        order_by="AnamnesisQuestion.order_index",
        cascade="all, delete-orphan",
    )


class AnamnesisQuestion(TenantModel):
    __tablename__ = "anamnesis_questions"

    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("anamnesis_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=QuestionFieldType.YES_NO.value
    )
    options: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_risk_alert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_trigger_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    template: Mapped["AnamnesisTemplate"] = relationship(
        "AnamnesisTemplate",
        back_populates="questions",
    )


class AnamnesisSubmission(TenantModel):
    __tablename__ = "anamnesis_submissions"

    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("anamnesis_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    booking_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    public_token: Mapped[str] = mapped_column(
        String(64),
        default=_generate_public_token,
        unique=True,
        nullable=False,
        index=True,
    )
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    has_risk_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_alerts_summary: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    signature_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signature_image: Mapped[str | None] = mapped_column(Text, nullable=True)
    tcle_accepted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    tcle_accepted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
