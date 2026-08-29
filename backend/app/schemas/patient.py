from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import InputSchema, OutputSchema


class PatientCreate(InputSchema):
    name: str = Field(min_length=1)
    phone: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    notes: str | None = None


class PatientUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    notes: str | None = None
    consent_whatsapp: bool | None = None


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
