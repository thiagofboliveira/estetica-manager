import time

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    bookings,
    dashboard,
    export,
    financial_settings,
    fixed_expenses,
    patients,
    payment_fee_rules,
    procedures,
    reports,
    retention,
    sales,
    sessions,
    super_admin,
    system,
    users,
)
from app.core.config import settings

app = FastAPI(title="Estetica API", version="0.1.0")

if settings.ENV == "development":
    # Só em dev: em produção o front é servido de um domínio fixo e
    # conhecido, configurado explicitamente — nunca "*".
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Rota pública — não declara DbSession, então não passa pela
    validação de JWT nem exige tenant."""
    return {"status": "ok"}


from pydantic import BaseModel

from app.db.session import unsafe_session_without_tenant
from app.repositories.user import UserRepository


class DevLoginPayload(BaseModel):
    email: str | None = None
    password: str | None = None


if settings.ENV == "development":
    dev_secret = settings.DEV_AUTH_SECRET or "dev-secret-estetica-local-key-superadmin-2026"

    @app.post("/dev/login", tags=["dev"])
    def dev_login(payload: DevLoginPayload | None = None) -> dict[str, str]:
        """SOMENTE dev local sem Supabase (ver core/security.py)."""
        now = int(time.time())
        user_id = "00000000-0000-0000-0000-000000000001"

        with unsafe_session_without_tenant("dev_login authentication") as db_sess:
            user_repo = UserRepository(db_sess)
            target_user = None
            if payload and payload.email:
                target_user = user_repo.get_by_email(payload.email.strip().lower())
            if not target_user:
                users = user_repo.list_all()
                if users:
                    target_user = users[0]
            if target_user:
                user_id = str(target_user.id)

        token = jwt.encode(
            {
                "sub": user_id,
                "aud": settings.SUPABASE_JWT_AUDIENCE,
                "role": settings.SUPABASE_JWT_AUDIENCE,
                "iat": now,
                "exp": now + 3600 * 24,
            },
            dev_secret,
            algorithm="HS256",
        )
        return {"access_token": token}

    from uuid import UUID as _UUID

    from fastapi import Depends as _Depends
    from fastapi.security import HTTPAuthorizationCredentials as _HTTPCreds
    from fastapi.security import HTTPBearer as _HTTPBearer


    @app.post("/dev/impersonate/{user_id}", tags=["dev"])
    def dev_impersonate(
        user_id: str,
        creds: _HTTPCreds = _Depends(_HTTPBearer()),
    ) -> dict[str, str]:
        """Gera um token de impersonação para um usuário específico.
        Exige que o chamador seja um Super Admin autenticado.
        SOMENTE disponível em ENV=development.
        """
        from fastapi import HTTPException as _HTTPEx
        from fastapi import status as _status

        from app.core.security import _decode as _sec_decode
        from app.db.session import unsafe_session_without_tenant as _unsafe_sess

        # Valida que quem chama é superadmin
        claims = _sec_decode(creds.credentials)
        caller_id = claims.get("sub")

        with _unsafe_sess("dev_impersonate auth check") as db_sess:
            caller_repo = UserRepository(db_sess)
            caller = caller_repo.get_by_id(_UUID(caller_id))
            if not caller or (caller.role != "superadmin" and not caller.is_superuser):
                raise _HTTPEx(
                    status_code=_status.HTTP_403_FORBIDDEN,
                    detail="Apenas Super Admin pode impersonar usuários",
                )

            target = caller_repo.get_by_id(_UUID(user_id))
            if not target:
                raise _HTTPEx(
                    status_code=_status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado",
                )

        now = int(time.time())
        token = jwt.encode(
            {
                "sub": user_id,
                "aud": settings.SUPABASE_JWT_AUDIENCE,
                "role": settings.SUPABASE_JWT_AUDIENCE,
                "iat": now,
                "exp": now + 3600 * 8,
                "impersonated_by": caller_id,
            },
            dev_secret,
            algorithm="HS256",
        )
        return {"access_token": token}


app.include_router(patients.router, prefix="/api/v1")
app.include_router(procedures.router, prefix="/api/v1")
app.include_router(financial_settings.router, prefix="/api/v1")
app.include_router(payment_fee_rules.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(retention.router, prefix="/api/v1")
app.include_router(fixed_expenses.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(super_admin.router, prefix="/api/v1")
