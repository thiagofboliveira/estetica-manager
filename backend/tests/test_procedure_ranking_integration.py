"""Teste de integração REAL contra o Postgres do Docker (não mockado).

Ranking de procedimentos: session_count (I5 — atendimento é Sessão
COMPLETED, não SaleItem.quantity) e paginação. Mesmo padrão de
tests/test_sales_integration.py.
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


@pytest.fixture
def patient_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/patients",
        json={"name": f"Paciente Teste {uuid.uuid4()}"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.fixture
def procedure_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/procedures",
        json={
            "name": f"Procedimento Ranking {uuid.uuid4()}",
            "price": "1000.00",
            "estimated_cost": "300.00",
        },
        headers=auth_headers,
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


class TestSessionCountEhSessaoCompletedNaoQuantidadeVendida:
    def test_sessao_scheduled_nao_conta_como_atendimento(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        client.post("/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers)

        resp = client.get(
            "/api/v1/reports/procedures?period=today&page_size=100",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        row = next(r for r in resp.json()["rows"] if r["procedure_id"] == procedure_id)
        # A venda foi registrada e o item existe no ranking (gross_revenue > 0),
        # mas a sessão ainda está SCHEDULED — não é um atendimento realizado.
        assert row["gross_revenue"] == "1000.00"
        assert row["session_count"] == 0

    def test_sessao_completed_conta_exatamente_uma_vez(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        sale_resp = client.post(
            "/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers
        )
        session_id = sale_resp.json()["sessions"][0]["id"]

        patch_resp = client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"status": "COMPLETED"},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200, patch_resp.text

        resp = client.get(
            "/api/v1/reports/procedures?period=today&page_size=100",
            headers=auth_headers,
        )
        row = next(r for r in resp.json()["rows"] if r["procedure_id"] == procedure_id)
        assert row["session_count"] == 1


class TestPaginacao:
    def test_page_size_limita_linhas_retornadas(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/reports/procedures?period=this_month&page=1&page_size=2",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["rows"]) <= 2
        assert body["page"] == 1
        assert body["page_size"] == 2
        # total_count reflete o total real, não o tamanho da página.
        assert body["total_count"] >= len(body["rows"])

    def test_pagina_alem_do_total_devolve_lista_vazia_nao_erro(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/reports/procedures?period=this_month&page=99999&page_size=10",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["rows"] == []
