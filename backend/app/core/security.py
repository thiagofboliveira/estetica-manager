"""Validação de JWT do Supabase. O backend VALIDA tokens, nunca emite.

professional_id vem SEMPRE do claim `sub` — nunca de path/query/header/
body (ver ../../ENGENHARIA.md, invariante I2). Esta é a única origem de
tenant na aplicação inteira.
"""

from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import settings

_bearer = HTTPBearer(auto_error=True)


@lru_cache(maxsize=1)
def _jwk_client() -> PyJWKClient:
    """Cache de chaves com refetch automático em rotação (kid desconhecido).

    lifespan=600 casa com o cache do edge do Supabase: mais longo rejeita
    token válido após rotação, mais curto vira 1 HTTP por chamada de API.
    """
    return PyJWKClient(
        f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
        cache_keys=True,
        lifespan=600,
        max_cached_keys=8,
    )


def _decode_dev(token: str) -> dict:
    """Modo dev local: token HS256 assinado com dev_secret, sem
    Supabase. SÓ é alcançado quando ENV=development — em produção esta função nunca é chamada (ver _decode).
    """
    dev_secret = settings.DEV_AUTH_SECRET or "dev-secret-estetica-local-key-superadmin-2026"
    try:
        return jwt.decode(
            token,
            dev_secret,
            algorithms=["HS256"],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            options={"require": ["exp", "sub", "aud"], "verify_exp": True},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _decode(token: str) -> dict:
    if settings.ENV == "development":
        return _decode_dev(token)

    try:
        signing_key = _jwk_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            # Lista explícita — nunca aceite o alg do header do token nem
            # inclua "none" (bypass clássico de verificação).
            algorithms=["ES256", "RS256"],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
            options={
                "require": ["exp", "sub", "aud", "iss"],
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_signature": True,
            },
        )
    except jwt.PyJWTError as exc:
        # Mensagem genérica de propósito: distinguir "expirado" de
        # "assinatura inválida" entrega informação a quem sonda a API.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_professional_id(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UUID:
    """ÚNICA origem de professional_id na aplicação inteira.

    O `sub` do Supabase é o auth.users.id. Assumimos mapeamento 1:1
    User <-> Professional — se o produto ganhar multi-profissional
    (visão, Estágio 3), este é o único ponto que muda: uma consulta
    resolvendo user_id -> professional_id.
    """
    claims = _decode(creds.credentials)

    if claims.get("role") != settings.SUPABASE_JWT_AUDIENCE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Role não autorizada")

    try:
        return UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Claim sub inválido") from exc
