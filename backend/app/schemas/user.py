from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import InputSchema, OutputSchema


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


class UserOutput(OutputSchema):
    id: UUID
    clinic_id: UUID | None = None
    clinic_name: str | None = None
    name: str
    email: str
    role: str
    is_superuser: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
