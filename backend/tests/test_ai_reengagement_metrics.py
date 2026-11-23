# ruff: noqa: F811
"""AI-06 (reengajamento), AI-05 (medição) e a checagem de números da IA."""

import uuid

import pytest

from app.domain.ai.grounding import allowed_numbers, is_grounded, numbers_in
from tests.test_ai_draft_message import (  # noqa: F401 — fixtures reutilizadas
    FakeProvider,
    _opportunity,
    auth_headers,
    client,
    professional_id,
    provider,
)


def _patient(client, headers, *, consent: bool = True) -> str:
    resp = client.post(
        "/api/v1/patients",
        json={
            "name": f"Beatriz Lima {uuid.uuid4().hex[:6]}",
            "phone": "31988887777",
            "consent_whatsapp": consent,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _draft(client, headers, patient_id, kind="inactive"):
    return client.post(
        f"/api/v1/retention/reengagement/{patient_id}/draft-message",
        params={"kind": kind},
        headers=headers,
    )


def _usage(client, headers) -> dict:
    resp = client.get("/api/v1/ai/usage", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestGrounding:
    def test_numeros_equivalentes_em_formatos_diferentes(self) -> None:
        assert numbers_in("R$ 1.234,50") == numbers_in("1234.50")

    def test_texto_sem_numero_passa(self) -> None:
        assert is_grounded("Oi, Ana! Vamos marcar?", set())

    def test_numero_inventado_reprova(self) -> None:
        allowed = allowed_numbers("1200.00", 3)
        assert is_grounded("Faturou R$ 1.200,00 em 3 vendas", allowed)
        assert not is_grounded("Faturou R$ 1.500,00 em 3 vendas", allowed)

    def test_zeros_a_esquerda_nao_enganam(self) -> None:
        assert is_grounded("5", allowed_numbers("05"))


class TestReengagementDraft:
    @pytest.mark.parametrize("kind", ["inactive", "never_treated"])
    def test_gera_rascunho(
        self, client, auth_headers, provider, kind  # noqa: F811
    ) -> None:
        pid = _patient(client, auth_headers)
        resp = _draft(client, auth_headers, pid, kind)
        assert resp.status_code == 200, resp.text
        assert resp.json()["source"] == "ai"
        assert len(provider.calls) == 1

    def test_payload_so_leva_primeiro_nome(
        self, client, auth_headers, provider  # noqa: F811
    ) -> None:
        pid = _patient(client, auth_headers)
        _draft(client, auth_headers, pid)
        sent = provider.calls[0]["system"] + provider.calls[0]["user"]
        assert "Beatriz" in sent
        assert "Lima" not in sent and "31988887777" not in sent and "R$" not in sent

    def test_sem_consentimento_422_e_nao_chama_ia(
        self, client, auth_headers, provider  # noqa: F811
    ) -> None:
        pid = _patient(client, auth_headers, consent=False)
        assert _draft(client, auth_headers, pid).status_code == 422
        assert provider.calls == []

    def test_paciente_inexistente_404(self, client, auth_headers, provider) -> None:  # noqa: F811
        assert _draft(client, auth_headers, str(uuid.uuid4())).status_code == 404

    def test_kind_invalido_422(self, client, auth_headers, provider) -> None:  # noqa: F811
        pid = _patient(client, auth_headers)
        assert _draft(client, auth_headers, pid, "qualquer").status_code == 422

    def test_texto_com_numero_e_descartado(
        self, client, auth_headers, provider  # noqa: F811
    ) -> None:
        provider.reply = "Oi! Tenho 30% de desconto para você."
        pid = _patient(client, auth_headers)
        body = _draft(client, auth_headers, pid).json()
        assert body["source"] == "fallback"
        assert "30%" not in body["text"]


class TestUsageMetrics:
    def test_conta_gerados_enviados_editados_e_texto_padrao(
        self, client, auth_headers, professional_id, provider  # noqa: F811
    ) -> None:
        before = _usage(client, auth_headers)
        opp = _opportunity(client, auth_headers, professional_id)

        # um rascunho da IA
        assert client.post(
            f"/api/v1/retention/opportunities/{opp}/draft-message",
            headers=auth_headers,
        ).json()["source"] == "ai"
        # um que cai no texto padrão
        provider.fail = True
        client.post(
            f"/api/v1/retention/opportunities/{opp}/draft-message",
            headers=auth_headers,
        )
        # enviados: um como veio, um editado
        for outcome in ("sent", "sent_edited"):
            r = client.post(
                "/api/v1/ai/drafts/feedback",
                json={"outcome": outcome},
                headers=auth_headers,
            )
            assert r.status_code == 204

        after = _usage(client, auth_headers)
        assert after["generated"] == before["generated"] + 1
        assert after["fallbacks"] == before["fallbacks"] + 1
        assert after["sent"] == before["sent"] + 2
        assert after["sent_edited"] == before["sent_edited"] + 1
        assert after["remaining"] == after["limit"] - after["generated"]

    def test_feedback_com_valor_invalido_422(self, client, auth_headers, provider) -> None:  # noqa: F811
        r = client.post(
            "/api/v1/ai/drafts/feedback", json={"outcome": "x"}, headers=auth_headers
        )
        assert r.status_code == 422

    def test_exige_autenticacao(self, client) -> None:  # noqa: F811
        assert client.get("/api/v1/ai/usage").status_code in (401, 403)
        assert client.post(
            "/api/v1/ai/drafts/feedback", json={"outcome": "sent"}
        ).status_code in (401, 403)
