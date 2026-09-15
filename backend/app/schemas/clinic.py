from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import InputSchema, OutputSchema


class ClinicCreateInput(InputSchema):
    name: str = Field(min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    plan: str = Field(default="standard", max_length=50)

    @field_validator("document", "phone", "email", mode="before")
    @classmethod
    def sanitize_optional_fields(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v


class ClinicUpdateInput(InputSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    plan: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None

    @field_validator("name", "document", "phone", "email", "plan", mode="before")
    @classmethod
    def sanitize_optional_fields(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v


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
