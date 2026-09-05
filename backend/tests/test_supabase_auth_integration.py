"""B-03 — o caminho real de auth (Supabase Auth + JWKS) nunca tinha sido
exercitado por nenhum dos testes deste projeto.

Ver docs/pending/BACKLOG_GO_LIVE.md B-03/B-03a. Todos os outros 264
testes rodam via /dev/login (ENV=development, HS256 local) — nenhum
provava que _decode() em ENV=production, validando um JWT ES256 real
contra o JWKS do Supabase, de fato autoriza uma chamada.

Requer, além do Postgres real:
  - SUPABASE_TEST_EMAIL / SUPABASE_TEST_PASSWORD no .env: credenciais de
    um usuário REAL do Supabase Auth deste projeto (nunca commitar).
  - Uma linha em `users`/`professionals` no Postgres local com o MESMO id
    do usuário no Supabase Auth (o app não tem signup público ainda —
    B-02 —, então esse vínculo é manual: ver o UID em Authentication →
    Users no painel do Supabase).

Sem as credenciais, os testes pulam com skip — nunca falham. É o mesmo
padrão de DEV_AUTH_SECRET para o modo dev (test_sales_integration.py).
"""

import importlib

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not (
        settings.SUPABASE_TEST_EMAIL
        and settings.SUPABASE_TEST_PASSWORD
        and settings.SUPABASE_TEST_ANON_KEY
    ),
    reason=(
        "requer SUPABASE_TEST_EMAIL + SUPABASE_TEST_PASSWORD + "
        "SUPABASE_TEST_ANON_KEY no .env (credenciais de um usuário real "
        "do Supabase Auth) — ver docstring"
    ),
)


@pytest.fixture
def production_app(monkeypatch: pytest.MonkeyPatch):
    """App recarregado com ENV=production: só assim _decode() usa o
    branch real do JWKS em vez do HS256 fake de dev (security.py:58)."""
    monkeypatch.setenv("ENV", "production")

    import app.core.config

    app.core.config.get_settings.cache_clear()
    importlib.reload(app.core.config)
    import app.core.security

    importlib.reload(app.core.security)
    import app.main

    reloaded = importlib.reload(app.main)

    yield reloaded.app

    # Devolve ao modo dev para não vazar estado a outros arquivos de teste.
    monkeypatch.undo()
    app.core.config.get_settings.cache_clear()
    importlib.reload(app.core.config)
    importlib.reload(app.core.security)
    importlib.reload(app.main)


@pytest.fixture
def real_access_token() -> str:
    """Login de verdade contra o Supabase Auth REST — mesmo endpoint que
    supabase-js chama em signInWithPassword() no frontend."""
    resp = httpx.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "password"},
        headers={"apikey": settings.SUPABASE_TEST_ANON_KEY},
        json={
            "email": settings.SUPABASE_TEST_EMAIL,
            "password": settings.SUPABASE_TEST_PASSWORD,
        },
        timeout=10,
    )
    assert resp.status_code == 200, (
        f"login real no Supabase falhou ({resp.status_code}): {resp.text} — "
        "confira SUPABASE_TEST_EMAIL/PASSWORD e se o usuário existe no painel"
    )
    token = resp.json().get("access_token")
    assert token, f"resposta do Supabase sem access_token: {resp.json()}"
    return token


class TestLoginRealViaSupabase:
    def test_token_real_autoriza_chamada_autenticada(
        self, production_app, real_access_token: str
    ) -> None:
        """O teste central de B-03: um JWT genuíno do Supabase, validado
        via JWKS em ENV=production, autoriza uma chamada real à API."""
        client = TestClient(production_app)

        resp = client.get(
            "/api/v1/patients", headers={"Authorization": f"Bearer {real_access_token}"}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "items" in body and "total_count" in body

    def test_token_real_autoriza_escrita(
        self, production_app, real_access_token: str
    ) -> None:
        """Confirma que não é só leitura: o professional_id extraído do
        token real também autoriza INSERT com RLS ativo."""
        client = TestClient(production_app)

        resp = client.post(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {real_access_token}"},
            json={"name": "B-03 Supabase Real — pytest"},
        )
        assert resp.status_code == 201, resp.text

        # Limpeza: não deixar dado de teste acumulando no Postgres real.
        patient_id = resp.json()["id"]
        client.delete(
            f"/api/v1/patients/{patient_id}",
            headers={"Authorization": f"Bearer {real_access_token}"},
        )

    def test_token_adulterado_e_rejeitado_em_producao(self, production_app) -> None:
        """Contraprova: em ENV=production, um token qualquer (não
        assinado pelo Supabase) tem de falhar — sem isso o teste anterior
        provaria pouco (poderia estar validando qualquer coisa)."""
        client = TestClient(production_app)

        resp = client.get(
            "/api/v1/patients", headers={"Authorization": "Bearer token.forjado.aqui"}
        )
        assert resp.status_code == 401

    def test_sem_token_e_rejeitado_em_producao(self, production_app) -> None:
        client = TestClient(production_app)
        resp = client.get("/api/v1/patients")
        assert resp.status_code in (401, 403)
