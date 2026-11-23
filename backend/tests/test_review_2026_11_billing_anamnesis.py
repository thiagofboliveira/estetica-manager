"""Regressões da revisão de código de 2026-11-23 (REV-01, REV-02, REV-03, REV-05)."""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestWebhookFailClosed:
    def test_sem_segredo_configurado_recusa(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REV-01: sem ASAAS_WEBHOOK_SECRET o webhook NÃO pode aceitar ninguém."""
        monkeypatch.setattr(settings, "ASAAS_WEBHOOK_SECRET", None)
        resp = client.post(
            "/api/v1/billing/webhooks/asaas",
            json={"event": "PAYMENT_CONFIRMED", "payment": {"subscription": "x"}},
        )
        assert resp.status_code == 503

    def test_corpo_invalido_vira_400(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "ASAAS_WEBHOOK_SECRET", "segredo-de-teste")
        resp = client.post(
            "/api/v1/billing/webhooks/asaas",
            content=b"nao-e-json",
            headers={
                "asaas-access-token": "segredo-de-teste",
                "content-type": "application/json",
            },
        )
        assert resp.status_code == 400


class TestCheckoutIdempotente:
    def test_segundo_checkout_nao_cria_outra_assinatura(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """REV-02: duplo clique não pode gerar duas assinaturas recorrentes."""
        # O banco de teste pode já ter assinatura de outro ciclo (estado herdado
        # de outros testes): usa o primeiro ciclo que o checkout aceitar.
        first = payload = None
        for cycle in ("MONTHLY", "QUARTERLY", "YEARLY"):
            payload = {"cycle": cycle, "billing_type": "PIX"}
            first = client.post(
                "/api/v1/billing/checkout", json=payload, headers=auth_headers
            )
            if first.status_code != 409:
                break
        assert first.status_code in (200, 201), first.text
        second = client.post("/api/v1/billing/checkout", json=payload, headers=auth_headers)
        assert second.status_code in (200, 201), second.text
        assert second.json()["subscription_id"] == first.json()["subscription_id"]
        assert second.json()["invoice_url"] == first.json()["invoice_url"]

    def test_erro_do_gateway_nao_vaza_ao_cliente(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.billing_service import BillingService

        def boom(*_a, **_k):
            raise RuntimeError("SEGREDO-INTERNO api_key=abc123")

        monkeypatch.setattr(BillingService, "checkout", boom)
        resp = client.post(
            "/api/v1/billing/checkout",
            json={"cycle": "MONTHLY", "billing_type": "PIX"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "SEGREDO-INTERNO" not in resp.text


class TestAnamneseImutavelAposEnvio:
    def _submit_payload(self, questions: list[dict], name: str) -> dict:
        answers = {q["id"]: "não" for q in questions}
        for q in questions:
            if q["field_type"] in ("text", "long_text"):
                answers[q["id"]] = "Tratamento facial preventivo"
        return {
            "patient_name": name,
            "patient_phone": "11999998888",
            "answers": answers,
            "signature_name": "Maria Teste Silva",
            "signature_image": "data:image/png;base64,assinado",
            "tcle_accepted": True,
        }

    def test_reenvio_e_bloqueado_e_original_preservado(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """REV-03: ficha enviada não pode ser sobrescrita por quem tem o link."""
        name = f"Paciente Imutavel {uuid.uuid4()}"
        token = client.post(
            "/api/v1/anamnesis/submissions/token",
            params={"patient_name": name, "patient_phone": "11999998888"},
            headers=auth_headers,
        ).json()["public_token"]
        questions = client.get(f"/api/v1/public/anamnesis/{token}").json()["questions"]
        payload = self._submit_payload(questions, name)

        ok = client.post(f"/api/v1/public/anamnesis/{token}", json=payload)
        assert ok.status_code == 200, ok.text
        original_at = ok.json()["tcle_accepted_at"]

        tampered = dict(payload, signature_name="Outra Pessoa")
        again = client.post(f"/api/v1/public/anamnesis/{token}", json=tampered)
        assert again.status_code == 409

        form = client.get(f"/api/v1/public/anamnesis/{token}").json()
        assert form["is_submitted"] is True
        resp_list = client.get("/api/v1/anamnesis/submissions", headers=auth_headers)
        mine = next(s for s in resp_list.json() if s["public_token"] == token)
        assert mine["signature_name"] == "Maria Teste Silva"
        assert datetime.fromisoformat(mine["tcle_accepted_at"]) == datetime.fromisoformat(
            original_at
        )

    def test_assinatura_gigante_e_rejeitada(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """REV-05: rota pública não aceita payload arbitrariamente grande."""
        name = f"Paciente Grande {uuid.uuid4()}"
        token = client.post(
            "/api/v1/anamnesis/submissions/token",
            params={"patient_name": name, "patient_phone": "11999998888"},
            headers=auth_headers,
        ).json()["public_token"]
        questions = client.get(f"/api/v1/public/anamnesis/{token}").json()["questions"]
        payload = self._submit_payload(questions, name)
        payload["signature_image"] = "data:image/png;base64," + "A" * 500_000
        resp = client.post(f"/api/v1/public/anamnesis/{token}", json=payload)
        assert resp.status_code == 422


class TestRotasPublicasEndurecidas:
    def test_corpo_gigante_em_rota_publica_vira_413(self, client: TestClient) -> None:
        """REV-05: teto global de corpo nas rotas /public."""
        big = b'{"x":"' + b"A" * (3 * 1024 * 1024) + b'"}'
        resp = client.post(
            "/api/v1/public/anamnesis/qualquercoisa123",
            content=big,
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 413

    def test_token_do_agendamento_aceito_por_header(self, client: TestClient) -> None:
        """REV-06: o token não precisa mais ir na query string."""
        bid = uuid.uuid4()
        # token inexistente: 404 prova que o header foi lido (sem token seria 422)
        resp = client.get(
            f"/api/v1/public/bookings/{bid}",
            headers={"X-Booking-Token": "token-que-nao-existe-123"},
        )
        assert resp.status_code == 404
        sem = client.get(f"/api/v1/public/bookings/{bid}")
        assert sem.status_code == 422

    def test_token_na_query_continua_funcionando_deprecado(
        self, client: TestClient
    ) -> None:
        bid = uuid.uuid4()
        resp = client.get(
            f"/api/v1/public/bookings/{bid}", params={"token": "token-que-nao-existe-123"}
        )
        assert resp.status_code == 404


class TestCupomRateLimit:
    def test_validacao_de_cupom_tem_limite(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """REV-10: 30/hora por profissional; a 31ª vira 429."""
        from app.api import deps

        deps._coupon_validate_rate_limiter._calls.clear()
        codes = []
        for i in range(31):
            r = client.post(
                "/api/v1/billing/coupons/validate",
                json={"code": f"NAO_EXISTE_{i}", "cycle": "monthly"},
                headers=auth_headers,
            )
            codes.append(r.status_code)
        deps._coupon_validate_rate_limiter._calls.clear()
        assert codes[:30] == [200] * 30
        assert codes[30] == 429


class TestWebhookDedupe:
    def test_reentrega_do_mesmo_pagamento_nao_estende_periodo(self) -> None:
        """REV-11: CONFIRMED + RECEIVED da mesma cobrança contam uma vez."""
        from datetime import UTC, datetime

        from app.models.subscription import Subscription, SubscriptionStatus
        from app.services.billing_service import BillingService

        class _Repo:
            def __init__(self, sub):
                self.sub = sub

            def get_by_asaas_subscription_id(self, _id):
                return self.sub

            def get_by_asaas_customer_id(self, _id):
                return None

            def flush(self):
                pass

        sub = Subscription(
            status=SubscriptionStatus.TRIALING.value,
            cycle="MONTHLY",
            trial_ends_at=datetime.now(UTC),
        )
        svc = BillingService(
            subscription_repo=_Repo(sub), coupon_repo=None, clinic_repo=None
        )
        evt = {"id": "pay_1", "subscription": "sub_1"}
        svc.handle_asaas_webhook("PAYMENT_CONFIRMED", evt)
        first_end = sub.current_period_end
        assert sub.status == SubscriptionStatus.ACTIVE.value
        svc.handle_asaas_webhook("PAYMENT_RECEIVED", evt)
        assert sub.current_period_end == first_end
        svc.handle_asaas_webhook(
            "PAYMENT_RECEIVED", {"id": "pay_2", "subscription": "sub_1"}
        )
        assert sub.current_period_end >= first_end
        assert sub.last_payment_id == "pay_2"
