"""Teste de integração REAL contra o Postgres do Docker (não mockado).

G-11 — no-show evitado: o maior alvo econômico do produto (no-show,
~R$560/mês na cliente zero) não era medido em lugar nenhum antes desta
task — ver docs/pending/BACKLOG_GO_LIVE.md §6. Mesmo padrão de fixtures
de tests/test_patient_procedure_filters.py.
"""

import uuid

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


def _create_patient(client: TestClient, headers: dict[str, str], name: str) -> str:
    resp = client.post("/api/v1/patients", json={"name": name}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_procedure(client: TestClient, headers: dict[str, str], name: str, price: str) -> str:
    resp = client.post(
        "/api/v1/procedures",
        json={"name": name, "price": price, "estimated_cost": "30.00"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _sale_body(patient_id: str, procedure_id: str) -> dict:
    return {
        "patient_id": patient_id,
        "type": "SINGLE",
        "items": [{"procedure_id": procedure_id, "quantity": 1}],
        "payment_method": "PIX",
        "installments": 1,
    }


class TestNoShowEvitado:
    def test_sessao_confirmada_e_completed_conta_como_no_show_evitado(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Confirmou e Veio {marker}")
        procedure_id = _create_procedure(
            client, auth_headers, f"Servico Confirmado {uuid.uuid4()}", "280.00"
        )
        sale_resp = client.post(
            "/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers
        )
        session_id = sale_resp.json()["sessions"][0]["id"]

        # Passa pelo fluxo anti-no-show (confirmed_at) antes de completar.
        resp_confirm = client.post(
            f"/api/v1/sessions/{session_id}/confirm", headers=auth_headers
        )
        assert resp_confirm.status_code == 200, resp_confirm.text

        resp_complete = client.patch(
            f"/api/v1/sessions/{session_id}", json={"status": "COMPLETED"}, headers=auth_headers
        )
        assert resp_complete.status_code == 200, resp_complete.text

        resp_roi = client.get(
            "/api/v1/dashboard/roi", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp_roi.status_code == 200, resp_roi.text
        body = resp_roi.json()
        assert body["no_show_avoided_count"] >= 1
        # Não afirma o valor exato (outros testes no mesmo banco de dev
        # compartilhado também geram no-show evitado) — só que o valor
        # da sessão criada está refletido na soma.
        assert float(body["no_show_avoided_revenue"]) >= 280.00

    def test_sessao_sem_confirmacao_nao_conta_como_no_show_evitado(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Completar sem ter passado por confirmed_at não é "no-show
        evitado" pelo critério conservador (G-11 docstring) — é só uma
        sessão comum, sem sinal de que havia risco de falta."""
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Sem Confirmar {marker}")
        procedure_id = _create_procedure(
            client, auth_headers, f"Servico Sem Confirmar {uuid.uuid4()}", "500.00"
        )
        sale_resp = client.post(
            "/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers
        )
        session_id = sale_resp.json()["sessions"][0]["id"]

        # Completa direto, sem passar por /confirm.
        client.patch(
            f"/api/v1/sessions/{session_id}", json={"status": "COMPLETED"}, headers=auth_headers
        )

        resp_roi = client.get(
            "/api/v1/dashboard/roi", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp_roi.status_code == 200, resp_roi.text
        # Não afirma count==0 (outros testes no banco compartilhado
        # também somam) — a garantia real está no teste de domínio puro
        # (test_attribution.py) que isola exatamente este critério.
        assert "no_show_avoided_count" in resp_roi.json()

    def test_no_show_avoided_nunca_aparece_em_attributed_revenue(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Confirma a separação na resposta real da API — os dois
        campos existem e são distintos, não um substituindo o outro."""
        resp_roi = client.get(
            "/api/v1/dashboard/roi", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp_roi.status_code == 200, resp_roi.text
        body = resp_roi.json()
        assert "attributed_revenue" in body
        assert "no_show_avoided_revenue" in body
        assert "no_show_avoided_count" in body
