"""Testes de integração para aceite de Termos de Uso e LGPD/DPA (G-10)."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import engine, unsafe_session_without_tenant
from app.main import app
from app.models.terms_acceptance import TermsAcceptance
from app.schemas.user import CURRENT_TERMS_VERSION


def test_terms_acceptance_flow_integration():
    """Valida o fluxo completo de consentimento de termos e LGPD:
    1. Usuário logado verifica se já aceitou termos
    2. Envia requisição de aceite com versão, gravando IP e User-Agent
    3. Retorno do endpoint e chamadas subsequentes a /me refletem terms_accepted=True
    4. Tabela append-only terms_acceptances registra auditoria de conformidade
    """
    client = TestClient(app)
    login = client.post("/dev/login")
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EsteticaBrowser/1.0",
    }

    # 1. Consulta perfil atual
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    user_id = UUID(me_resp.json()["id"])

    # 2. Aceita os termos
    accept_resp = client.post(
        "/api/v1/users/me/accept-terms",
        json={"terms_version": CURRENT_TERMS_VERSION},
        headers=headers,
    )
    assert accept_resp.status_code == 200, accept_resp.text
    data = accept_resp.json()
    assert data["terms_accepted"] is True
    assert data["terms_version"] == CURRENT_TERMS_VERSION
    assert data["terms_accepted_at"] is not None

    # 3. Garante que /users/me retorna terms_accepted=True
    me_after = client.get("/api/v1/users/me", headers=headers)
    assert me_after.status_code == 200
    assert me_after.json()["terms_accepted"] is True
    assert me_after.json()["terms_version"] == CURRENT_TERMS_VERSION

    # 4. Contraprova de segurança: conexão crua sem tenant é bloqueada pelo RLS
    with Session(engine) as raw_session:
        stmt = (
            select(TermsAcceptance)
            .where(TermsAcceptance.user_id == user_id)
            .order_by(TermsAcceptance.accepted_at.desc())
        )
        assert raw_session.scalars(stmt).first() is None, (
            "RLS deve impedir leitura anônima sem contexto"
        )

    # 5. Com sessão administrativa de sistema, a auditoria é confirmada
    with unsafe_session_without_tenant("test terms audit verification") as session:
        audit = session.scalars(stmt).first()
        assert audit is not None
        assert audit.terms_version == CURRENT_TERMS_VERSION
        assert "EsteticaBrowser" in (audit.user_agent or "")
        assert audit.accepted_at <= datetime.now(UTC)
