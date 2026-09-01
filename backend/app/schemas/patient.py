from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.phone import InvalidPhoneError, normalize_br_phone
from app.schemas.base import InputSchema, OutputSchema


class PatientCreate(InputSchema):
    name: str = Field(min_length=1)
    phone: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    notes: str | None = None
    consent_whatsapp: bool = False

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        try:
            return normalize_br_phone(v)
        except InvalidPhoneError as exc:
            raise ValueError("Número de telefone inválido (deve conter DDD + número)") from exc


class PatientUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    notes: str | None = None
    consent_whatsapp: bool | None = None

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        try:
            return normalize_br_phone(v)
        except InvalidPhoneError as exc:
            raise ValueError("Número de telefone inválido (deve conter DDD + número)") from exc


class PatientOut(OutputSchema):
    id: UUID
    name: str
    phone: str | None
    email: str | None
    birth_date: date | None
    notes: str | None
    consent_whatsapp: bool
    consent_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PatientBatchImportItem(InputSchema):
    name: str = Field(default="", description="Nome da paciente")
    phone: str | None = Field(default=None, description="Telefone ou WhatsApp com DDD")
    email: str | None = Field(default=None, description="E-mail de contato")
    notes: str | None = Field(default=None, description="Anotações / histórico prévio")


class PatientBatchImportRequest(InputSchema):
    patients: list[PatientBatchImportItem] = Field(
        min_length=1,
        max_length=100,
        description="Lista de pacientes a importar (máximo 100 por lote)",
    )


class PatientBatchImportError(OutputSchema):
    line: int
    reason: str


class PatientBatchImportResult(OutputSchema):
    created_count: int
    skipped_count: int
    errors: list[PatientBatchImportError]
    patients: list[PatientOut]
