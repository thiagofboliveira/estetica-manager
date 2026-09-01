from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import InputSchema, OutputSchema


class ClinicCreateInput(InputSchema):
    name: str = Field(min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    plan: str = Field(default="standard", max_length=50)


class ClinicUpdateInput(InputSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    plan: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class ClinicOutput(OutputSchema):
    id: UUID
    name: str
    document: str | None
    phone: str | None
    email: str | None
    plan: str
    is_active: bool
    users_count: int = 0
    created_at: datetime
    updated_at: datetime
