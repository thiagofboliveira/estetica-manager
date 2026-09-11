from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.phone import InvalidPhoneError, normalize_br_phone
from app.models.patient import Gender
from app.schemas.base import InputSchema, OutputSchema


class PatientCreate(InputSchema):
    name: str = Field(min_length=1)
    phone: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    notes: str | None = None
    consent_whatsapp: bool = False
    gender: Gender | None = None
    referred_by_id: UUID | None = None

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        try:
            return normalize_br_phone(v)
        except InvalidPhoneError as exc:
            raise ValueError(
                "Número de telefone inválido (deve conter DDD + número)"
            ) from exc


class PatientUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    notes: str | None = None
    consent_whatsapp: bool | None = None
    gender: Gender | None = None
    referred_by_id: UUID | None = None
    vip_tier: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        try:
            return normalize_br_phone(v)
        except InvalidPhoneError as exc:
            raise ValueError(
                "Número de telefone inválido (deve conter DDD + número)"
            ) from exc


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
    gender: Gender | None
    loyalty_points: int = 0
    vip_tier: str = "BRONZE"
    referral_code: str | None = None
    referred_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("loyalty_points", mode="before")
    @classmethod
    def default_loyalty_points(cls, v: int | None) -> int:
        return v if v is not None else 0

    @field_validator("vip_tier", mode="before")
    @classmethod
    def default_vip_tier(cls, v: str | None) -> str:
        return v if v is not None else "BRONZE"


class PatientListOut(OutputSchema):
    items: list[PatientOut]
    total_count: int
    page: int
    page_size: int


class PatientBatchImportItem(InputSchema):
    name: str = Field(default="", description="Nome da paciente")
    phone: str | None = Field(default=None, description="Telefone ou WhatsApp com DDD")
    email: str | None = Field(default=None, description="E-mail de contato")
    notes: str | None = Field(default=None, description="Anotações / histórico prévio")
    procedure_id: UUID | None = Field(
        default=None,
        description="Procedimento de referência para oportunidade de retorno",
    )
    last_visit_date: date | None = Field(
        default=None, description="Data da última visita para calcular data de retorno"
    )


class PatientBatchImportRequest(InputSchema):
    patients: list[PatientBatchImportItem] = Field(
        min_length=1,
        max_length=100,
        description="Lista de pacientes a importar (máximo 100 por lote)",
    )
    default_procedure_id: UUID | None = Field(
        default=None,
        description="Procedimento padrão a associar às pacientes importadas",
    )
    generate_return_opportunities: bool = Field(
        default=False,
        description="Se True, gera oportunidades de retorno retroativas (source=IMPORT) no dia 1",
    )


class PatientBatchImportError(OutputSchema):
    line: int
    reason: str


class PatientBatchImportResult(OutputSchema):
    created_count: int
    skipped_count: int
    opportunities_created_count: int = 0
    errors: list[PatientBatchImportError]
    patients: list[PatientOut]


class PatientBirthdayOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    patient_phone: str | None = None
    birth_date: date
    day: int
    month: int
    days_until: int
    is_today: bool
    formatted_date: str
    whatsapp_url: str | None = None

