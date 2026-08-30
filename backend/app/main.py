import time

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    bookings,
    dashboard,
    financial_settings,
    fixed_expenses,
    patients,
    payment_fee_rules,
    procedures,
    reports,
    retention,
    sales,
    sessions,
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


if settings.ENV == "development" and settings.DEV_AUTH_SECRET:

    @app.post("/dev/login", tags=["dev"])
    def dev_login() -> dict[str, str]:
        """SOMENTE dev local sem Supabase (ver core/security.py). Esta
        rota nem existe se ENV != development ou DEV_AUTH_SECRET vazio —
        não há como isto ser exposto em produção por engano de config.
        """
        now = int(time.time())
        token = jwt.encode(
            {
                "sub": "00000000-0000-0000-0000-000000000001",
                "aud": settings.SUPABASE_JWT_AUDIENCE,
                "role": settings.SUPABASE_JWT_AUDIENCE,
                "iat": now,
                "exp": now + 3600 * 8,
            },
            settings.DEV_AUTH_SECRET,
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
