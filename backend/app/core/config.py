from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Conexão da aplicação: role NÃO-owner, NOBYPASSRLS (T-057a).
    # RLS é ignorado silenciosamente se a app conectar como owner/service_role.
    DATABASE_URL: str

    # Conexão separada para Alembic, com o owner — RLS não pode bloquear ALTER TABLE.
    DATABASE_URL_MIGRATIONS: str

    SUPABASE_URL: str
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    DEFAULT_TIMEZONE: str = "America/Sao_Paulo"

    ENV: str = "development"

    # Só tem efeito com ENV=development — ver core/security.py.
    # Nunca definir em produção: nesse modo o token não é validado contra
    # o Supabase, só assinado com HS256 usando este segredo local.
    DEV_AUTH_SECRET: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
