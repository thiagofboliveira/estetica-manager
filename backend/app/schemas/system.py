from pydantic import EmailStr, Field

from app.schemas.base import InputSchema, OutputSchema


class SystemStatusOutput(OutputSchema):
    is_initialized: bool
    users_count: int


class SystemSetupInput(InputSchema):
    clinic_name: str = Field(min_length=1, max_length=255)
    admin_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str | None = Field(default=None, max_length=255)
