from pydantic import EmailStr, Field

from app.schemas.base import InputSchema, OutputSchema


class SystemStatusOutput(OutputSchema):
    is_initialized: bool
    users_count: int


class SystemSetupInput(InputSchema):
    # B-01: sem campo de senha — o Supabase Auth cria o usuário via
    # convite/magic-link (ver system_service.setup_root). Um campo de
    # senha aqui seria coletado e descartado, como era antes.
    clinic_name: str = Field(min_length=1, max_length=255)
    admin_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
