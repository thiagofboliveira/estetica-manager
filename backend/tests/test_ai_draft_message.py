"""AI-01 / AI-02 — rascunho de mensagem de retorno por IA.

Provedor sempre falso: nenhum teste faz chamada de rede. Banco Postgres real.
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.deps import get_text_provider
from app.core.config import settings
from app.core.security import _decode
from app.db.session import unsafe_session_without_tenant
from app.domain.ai.return_message import (
    MAX_MESSAGE_CHARS,
    ReturnMessageContext,
    build_user_prompt,
    clean_generated,
    fallback_message,
    first_name,
)
from app.domain.retention.enums import ReturnOpportunityStatus
from app.main import app
from app.models.return_opportunity import ReturnOpportunity

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


class FakeProvider:
    def __init__(self, reply: str | None = "Oi, Ana! Que tal retomarmos seu cuidado?"):
        self.reply = reply
        self.calls: list[dict] = []
        self.fail = False

    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None:
        self.calls.append({"system": system, "user": user})
        if self.fail:
            raise TimeoutError("provedor fora do ar")
        return self.reply


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def professional_id(auth_headers: dict[str, str]) -> str:
    return _decode(auth_headers["Authorization"].removeprefix("Bearer "))["sub"]


@pytest.fixture
def provider():
    fake = FakeProvider()
    app.dependency_overrides[get_text_provider] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_text_provider, None)


def _opportunity(
    client: TestClient,
    headers: dict[str, str],
    professional_id: str,
    *,
    consent: bool = True,
    days_overdue: int = 10,
) -> str:
    pat = client.post(
        "/api/v1/patients",
        json={
            "name": f"Ana Souza {uuid.uuid4().hex[:6]}",
            "phone": "31999990000",
            "consent_whatsapp": consent,
        },
        headers=headers,
    )
    assert pat.status_code == 201, pat.text
    proc = client.post(
        "/api/v1/procedures",
        json={
            "name": f"Limpeza de pele {uuid.uuid4().hex[:6]}",
            "price": "200.00",
            "estimated_cost": "50.00",
        },
        headers=headers,
    )
    assert proc.status_code == 201, proc.text
    opp_id = uuid.uuid4()
    with unsafe_session_without_tenant("test: criar oportunidade") as session:
        session.execute(
            text("SELECT set_config('app.professional_id', :pid, true)"),
            {"pid": professional_id},
        )
        session.add(
            ReturnOpportunity(
                id=opp_id,
                professional_id=uuid.UUID(professional_id),
                patient_id=uuid.UUID(pat.json()["id"]),
                procedure_id=uuid.UUID(proc.json()["id"]),
                due_date=date.today() - timedelta(days=days_overdue),
                status=ReturnOpportunityStatus.OPEN,
            )
        )
        session.flush()
    return str(opp_id)


def _draft(client: TestClient, headers: dict[str, str], opp_id: str):
    return client.post(
        f"/api/v1/retention/opportunities/{opp_id}/draft-message", headers=headers
    )


class TestDomain:
    def test_primeiro_nome(self) -> None:
        assert first_name("  Ana Maria Souza ") == "Ana"
        assert first_name("") == ""

    def test_fallback_menciona_procedimento_e_nome(self) -> None:
        ctx = ReturnMessageContext("Ana", "Limpeza de pele", 10)
        msg = fallback_message(ctx)
        assert "Ana" in msg and "Limpeza de pele" in msg

    def test_prompt_nao_leva_dinheiro_nem_telefone(self) -> None:
        prompt = build_user_prompt(ReturnMessageContext("Ana", "Limpeza", 10))
        assert "R$" not in prompt and "31999" not in prompt

    def test_clean_generated_descarta_vazio_e_longo(self) -> None:
        assert clean_generated(None) is None
        assert clean_generated("   ") is None
        assert clean_generated("x" * (MAX_MESSAGE_CHARS + 1)) is None
        assert clean_generated('  "Oi!"  ') == "Oi!"


class TestDraftEndpoint:
    def test_gera_rascunho_com_ia(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        opp_id = _opportunity(client, auth_headers, professional_id)
        resp = _draft(client, auth_headers, opp_id)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "ai"
        assert body["text"] == provider.reply
        assert body["fallback_reason"] is None
        assert len(provider.calls) == 1

    def test_payload_da_ia_nao_leva_dado_sensivel(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        opp_id = _opportunity(client, auth_headers, professional_id)
        _draft(client, auth_headers, opp_id)
        sent = provider.calls[0]["system"] + provider.calls[0]["user"]
        assert "31999990000" not in sent  # telefone
        assert "R$" not in sent and "200.00" not in sent  # dinheiro
        assert "Souza" not in sent  # só o primeiro nome

    def test_nao_altera_status_da_oportunidade(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        opp_id = _opportunity(client, auth_headers, professional_id)
        _draft(client, auth_headers, opp_id)
        items = client.get(
            "/api/v1/retention/opportunities",
            params={"view": "all"},
            headers=auth_headers,
        ).json()
        mine = next(i for i in items if i["id"] == opp_id)
        assert mine["status"] == "OPEN"

    def test_sem_provedor_devolve_texto_fixo(
        self, client, auth_headers, professional_id
    ) -> None:
        app.dependency_overrides[get_text_provider] = lambda: None
        try:
            opp_id = _opportunity(client, auth_headers, professional_id)
            body = _draft(client, auth_headers, opp_id).json()
        finally:
            app.dependency_overrides.pop(get_text_provider, None)
        assert body["source"] == "fallback"
        assert body["fallback_reason"] == "no_provider"
        assert "Ana" in body["text"]

    def test_erro_do_provedor_cai_no_texto_fixo_sem_500(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        provider.fail = True
        opp_id = _opportunity(client, auth_headers, professional_id)
        resp = _draft(client, auth_headers, opp_id)
        assert resp.status_code == 200
        assert resp.json()["source"] == "fallback"
        assert resp.json()["fallback_reason"] == "provider_error"

    def test_resposta_vazia_cai_no_texto_fixo(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        provider.reply = "   "
        opp_id = _opportunity(client, auth_headers, professional_id)
        assert _draft(client, auth_headers, opp_id).json()["source"] == "fallback"

    def test_sem_consentimento_whatsapp_422(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        opp_id = _opportunity(client, auth_headers, professional_id, consent=False)
        resp = _draft(client, auth_headers, opp_id)
        assert resp.status_code == 422
        assert provider.calls == []  # nem chega a chamar a IA

    def test_oportunidade_inexistente_404(
        self, client, auth_headers, provider
    ) -> None:
        assert _draft(client, auth_headers, str(uuid.uuid4())).status_code == 404

    def test_exige_autenticacao(self, client, provider) -> None:
        resp = client.post(
            f"/api/v1/retention/opportunities/{uuid.uuid4()}/draft-message"
        )
        assert resp.status_code in (401, 403)


class TestMonthlyCap:
    def test_teto_do_mes_cai_no_texto_fixo_e_nao_chama_ia(
        self, client, auth_headers, professional_id, provider, monkeypatch
    ) -> None:
        opp_id = _opportunity(client, auth_headers, professional_id)
        # Descobre quanto já foi usado neste mês e fixa o teto em +1.
        first = _draft(client, auth_headers, opp_id).json()
        assert first["source"] == "ai"
        used_total = settings.AI_MONTHLY_DRAFT_LIMIT - first["remaining_drafts"]
        monkeypatch.setattr(settings, "AI_MONTHLY_DRAFT_LIMIT", used_total + 1)

        second = _draft(client, auth_headers, opp_id).json()
        assert second["source"] == "ai"
        assert second["remaining_drafts"] == 0

        calls_before = len(provider.calls)
        third = _draft(client, auth_headers, opp_id).json()
        assert third["source"] == "fallback"
        assert third["fallback_reason"] == "limit_reached"
        assert len(provider.calls) == calls_before  # não gastou chamada

    def test_fallback_nao_consome_o_teto(
        self, client, auth_headers, professional_id, provider
    ) -> None:
        opp_id = _opportunity(client, auth_headers, professional_id)
        before = _draft(client, auth_headers, opp_id).json()["remaining_drafts"]
        provider.fail = True
        _draft(client, auth_headers, opp_id)  # falha: não conta
        provider.fail = False
        after = _draft(client, auth_headers, opp_id).json()["remaining_drafts"]
        assert after == before - 1  # só a chamada que deu certo contou


class TestAnthropicProvider:
    """Provedor real, com a rede substituída: confere o formato da chamada."""

    def test_monta_requisicao_e_le_o_texto(self, monkeypatch) -> None:
        import httpx

        from app.services.ai_text_service import AnthropicProvider

        seen: dict = {}

        def fake_post(url, *, headers, json, timeout):
            seen.update(url=url, headers=headers, json=json, timeout=timeout)
            return httpx.Response(
                200,
                json={"content": [{"type": "text", "text": "Oi, Ana!"}]},
                request=httpx.Request("POST", url),
            )

        monkeypatch.setattr(httpx, "post", fake_post)
        out = AnthropicProvider("chave-falsa", "modelo-x", 5.0).complete(
            system="s", user="u", max_tokens=100
        )
        assert out == "Oi, Ana!"
        assert seen["headers"]["x-api-key"] == "chave-falsa"
        assert seen["json"]["model"] == "modelo-x"
        assert seen["json"]["messages"] == [{"role": "user", "content": "u"}]
        assert seen["timeout"] == 5.0

    def test_erro_http_levanta_para_o_servico_cair_no_fallback(
        self, monkeypatch
    ) -> None:
        import httpx

        from app.services.ai_text_service import AnthropicProvider

        def fake_post(url, **_):
            return httpx.Response(529, request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", fake_post)
        with pytest.raises(httpx.HTTPStatusError):
            AnthropicProvider("k", "m", 5.0).complete(system="s", user="u", max_tokens=1)
