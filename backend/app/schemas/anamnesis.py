"""Schemas para Anamnese Digital (AN-03)."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.models.anamnesis import QuestionFieldType
from app.schemas.base import InputSchema, OutputSchema


class AnamnesisQuestionCreate(InputSchema):
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)
    field_type: str = Field(default=QuestionFieldType.YES_NO.value)
    options: list[str] | None = None
    is_required: bool = True
    is_risk_alert: bool = False
    risk_trigger_value: str | None = None
    order_index: int = 0

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v: str) -> str:
        valid_types = [t.value for t in QuestionFieldType]
        if v not in valid_types:
            raise ValueError(f"field_type deve ser um de {valid_types}")
        return v


class AnamnesisQuestionUpdate(InputSchema):
    title: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)
    field_type: str | None = None
    options: list[str] | None = None
    is_required: bool | None = None
    is_risk_alert: bool | None = None
    risk_trigger_value: str | None = None
    order_index: int | None = None
    is_active: bool | None = None

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_types = [t.value for t in QuestionFieldType]
        if v not in valid_types:
            raise ValueError(f"field_type deve ser um de {valid_types}")
        return v


class QuestionOrderUpdate(InputSchema):
    question_id: UUID
    order_index: int


class AnamnesisReorderQuestionsInput(InputSchema):
    questions: list[QuestionOrderUpdate]


class AnamnesisQuestionOut(OutputSchema):
    id: UUID
    template_id: UUID
    title: str
    description: str | None
    field_type: str
    options: list[str] | None
    is_required: bool
    is_risk_alert: bool
    risk_trigger_value: str | None
    order_index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AnamnesisTemplateUpdate(InputSchema):
    title: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)
    auto_request_on_booking: bool | None = None


class AnamnesisTemplateOut(OutputSchema):
    id: UUID
    title: str
    description: str | None
    is_default: bool
    is_active: bool
    auto_request_on_booking: bool
    created_at: datetime
    updated_at: datetime
    questions: list[AnamnesisQuestionOut] = []


class PublicAnamnesisSubmitInput(InputSchema):
    patient_name: str = Field(..., min_length=2, max_length=255)
    patient_phone: str | None = Field(None, max_length=30)
    answers: dict[str, str | bool | list[str] | None] = Field(default_factory=dict)
    signature_name: str | None = Field(None, max_length=255)


class AnamnesisSubmissionOut(OutputSchema):
    id: UUID
    template_id: UUID
    patient_id: UUID | None
    booking_id: UUID | None
    public_token: str
    patient_name: str
    patient_phone: str | None
    answers: dict
    has_risk_alerts: bool
    risk_alerts_summary: list
    signature_name: str | None
    submitted_at: datetime | None
    created_at: datetime


class PublicAnamnesisFormOut(OutputSchema):
    token: str
    clinic_name: str | None = None
    professional_name: str
    professional_slug: str | None = None
    template_title: str
    template_description: str | None = None
    patient_name: str | None = None
    patient_phone: str | None = None
    is_submitted: bool = False
    submitted_at: datetime | None = None
    questions: list[AnamnesisQuestionOut]
