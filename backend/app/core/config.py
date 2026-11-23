import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Conexão da aplicação: role NÃO-owner, NOBYPASSRLS (T-057a).
    # RLS é ignorado silenciosamente se a app conectar como owner/service_role.
    DATABASE_URL: str

    # Conexão separada para Alembic, com o owner — se omitida, usa DATABASE_URL.
    DATABASE_URL_MIGRATIONS: str | None = None

    @field_validator("DATABASE_URL", "DATABASE_URL_MIGRATIONS", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str | None) -> str | None:
        if not v:
            return v
        import re

        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg2://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = v.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Se a senha contiver # antes do @, escapa para %23 (evita quebrar a URL como fragmento)
        match = re.match(r"^(postgresql\+psycopg2://[^:]+:)(.*)@([^@]+)$", v)
        if match:
            prefix, password, rest = match.groups()
            password = password.replace("#", "%23")
            v = f"{prefix}{password}@{rest}"

        # Host direct do Supabase é IPv6-only (incompatível com Render Free):
        # converte para o Connection Pooler IPv4. O ref do projeto vem da
        # própria URL (db.<ref>.supabase.co) — nada de identificador fixo no
        # código. Região/host do pooler configuráveis (default: us-east-2).
        direct = re.search(r"db\.([a-z0-9]+)\.supabase\.co", v)
        if direct:
            ref = direct.group(1)
            pooler = os.environ.get(
                "SUPABASE_POOLER_HOST", "aws-0-us-east-2.pooler.supabase.com"
            )
            v = v.replace(f"db.{ref}.supabase.co", pooler)
            v = re.sub(r"://postgres:", f"://postgres.{ref}:", v)

        # No pooler o usuário PRECISA ser postgres.<ref>; sem o host direct na
        # URL, o ref vem de SUPABASE_URL (https://<ref>.supabase.co).
        if "pooler.supabase.com" in v and "://postgres:" in v:
            url_ref = re.match(
                r"https://([a-z0-9]+)\.supabase\.co", os.environ.get("SUPABASE_URL", "")
            )
            if url_ref:
                v = re.sub(r"://postgres:", f"://postgres.{url_ref.group(1)}:", v)

        return v

    SUPABASE_URL: str
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    # Só usado por app/core/supabase_admin.py (B-01), para criar o
    # usuário no Supabase Auth no fluxo de setup/signup — nunca para
    # validar token de request normal (isso é via JWKS público, sem
    # segredo nenhum, ver security.py). Chave MESTRA do projeto Supabase:
    # ignora RLS de lá, cria/apaga qualquer usuário. Sem default de
    # propósito — ausência deve falhar alto, não silenciar.
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    # URL do frontend para onde o link de convite/magic-link do Supabase
    # redireciona após a pessoa definir a senha (B-01). Em dev, a própria
    # tela de login local.
    FRONTEND_URL: str = "http://localhost:5173"

    DEFAULT_TIMEZONE: str = "America/Sao_Paulo"

    # B-04: domínios do frontend autorizados a chamar a API em produção
    # (CORS). Lista separada por vírgula, ex.:
    # "https://app.lumina.com.br,https://lumina-web.vercel.app". Vazio
    # por padrão — sem isso configurado, front e back em domínios
    # diferentes não se falam (o browser bloqueia), então esta variável
    # É parte do checklist de deploy, não opcional.
    ALLOWED_ORIGINS: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Default DENIEGA, não concede (S-01a): variável ausente ou com typo
    # no painel de deploy faz o app subir em modo produção, onde /dev/login
    # não existe e o token é validado contra o Supabase. O inverso —
    # default "development" — abria acesso de superadmin sem senha a quem
    # adivinhasse a URL. Configuração ausente nunca deve liberar.
    ENV: str = "production"

    # G-08: Monitoramento de erros e telemetria via Sentry.
    # Se vazio, a telemetria fica desativada de forma segura (fail-safe).
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

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
    SUPABASE_TEST_ANON_KEY: str | None = None
    # Configurações do Gateway Asaas v3
    ASAAS_API_KEY: str | None = None
    ASAAS_API_URL: str = "https://sandbox.asaas.com/api/v3"
    ASAAS_WEBHOOK_SECRET: str | None = None

    # IA de texto (AI-01). Sem nenhuma chave, tudo cai no texto fixo: o produto
    # não depende de provedor para funcionar. AI_PROVIDER aceita um nome ou uma
    # lista em ordem de preferência ("groq,anthropic"); vazio = usa o que tiver chave.
    AI_PROVIDER: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-haiku-5-5"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    # Qualquer endpoint no formato OpenAI (OpenRouter, Together, servidor próprio).
    AI_BASE_URL: str | None = None
    AI_API_KEY: str | None = None
    AI_MODEL: str = ""
    AI_TIMEOUT_SECONDS: float = 8.0
    # Teto de rascunhos por profissional por mês (protege a margem do plano).
    AI_MONTHLY_DRAFT_LIMIT: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
