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

    # Default DENIEGA, não concede (S-01a): variável ausente ou com typo
    # no painel de deploy faz o app subir em modo produção, onde /dev/login
    # não existe e o token é validado contra o Supabase. O inverso —
    # default "development" — abria acesso de superadmin sem senha a quem
    # adivinhasse a URL. Configuração ausente nunca deve liberar.
    ENV: str = "production"

    # Só tem efeito com ENV=development — ver core/security.py.
    # Nunca definir em produção: nesse modo o token não é validado contra
    # o Supabase, só assinado com HS256 usando este segredo local.
    # Sem default (S-01b): segredo com fallback é segredo público.
    DEV_AUTH_SECRET: str | None = None

    # Opcionais, só para tests/test_supabase_auth_integration.py (B-03):
    # credenciais de um usuário REAL do Supabase Auth deste projeto, para
    # provar o caminho JWKS de _decode() com um JWT genuíno, não um mock.
    # Sem elas o teste pula (skip), nunca falha — nunca commitar valores.
    SUPABASE_TEST_EMAIL: str | None = None
    SUPABASE_TEST_PASSWORD: str | None = None
    # A publishable/anon key (a mesma de frontend/.env.local) — só para
    # autenticar a chamada de teste. O backend em si nunca precisa dela
    # para validar token (só do JWKS público, via SUPABASE_URL).
    SUPABASE_TEST_ANON_KEY: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
