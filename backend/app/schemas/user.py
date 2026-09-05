from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, computed_field

from app.schemas.base import InputSchema, OutputSchema

CURRENT_TERMS_VERSION = "2026-09-v1"


class UserCreateInput(InputSchema):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role: str = Field(
        default="user", pattern=r"^(superadmin|admin|user|professional|receptionist)$"
    )
    is_superuser: bool = False
    clinic_id: UUID | None = None


class UserUpdateInput(InputSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    role: str | None = Field(
        default=None, pattern=r"^(superadmin|admin|user|professional|receptionist)$"
    )
    is_active: bool | None = None
    is_superuser: bool | None = None
    clinic_id: UUID | None = None


class TermsAcceptInput(InputSchema):
    terms_version: str = Field(default=CURRENT_TERMS_VERSION, max_length=32)


class UserOutput(OutputSchema):
    id: UUID
    clinic_id: UUID | None = None
    clinic_name: str | None = None
    name: str
    email: str
    role: str
    is_superuser: bool
    is_active: bool
    terms_accepted_at: datetime | None = None
    terms_version: str | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def terms_accepted(self) -> bool:
        return bool(
            self.terms_accepted_at is not None
            and self.terms_version == CURRENT_TERMS_VERSION
        )
