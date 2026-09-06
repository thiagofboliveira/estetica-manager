"""Testes de integração REAL para o simulador de preços e alerta de margem negativa (A-10 / A-11)."""

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


def test_simulacao_preco_margem_positiva(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/sales/simulate",
        json={
            "price": "200.00",
            "estimated_cost": "30.00",
            "payment_method": "PIX",
            "installments": 1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["gross_amount"] == "200.00"
    assert data["cost_provisioned"] == "30.00"
    assert data["net_profit"] == "170.00"
    assert data["is_negative_margin"] is False
    assert data["negative_margin_alert"] is None
    assert float(data["margin"]) > 0


def test_simulacao_preco_alerta_margem_negativa(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/sales/simulate",
        json={
            "price": "40.00",
            "estimated_cost": "50.00",
            "payment_method": "PIX",
            "installments": 1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert float(data["net_profit"]) < 0
    assert data["is_negative_margin"] is True
    assert data["negative_margin_alert"] is not None
    assert "Margem negativa" in data["negative_margin_alert"]
    assert "Prejuízo de R$ 10.00" in data["negative_margin_alert"]


def test_simulacao_com_procedimento_existente(client: TestClient, auth_headers: dict[str, str]) -> None:
    proc_resp = client.post(
        "/api/v1/procedures",
        json={
            "name": f"Proc Simulado {uuid.uuid4()}",
            "price": "300.00",
            "estimated_cost": "60.00",
            "session_plan": "SINGLE",
        },
        headers=auth_headers,
    )
    assert proc_resp.status_code == 201
    proc_id = proc_resp.json()["id"]

    # Simula passando só procedure_id (herda preço e custo)
    resp = client.post(
        "/api/v1/sales/simulate",
        json={
            "procedure_id": proc_id,
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["price"] == "300.00"
    assert data["estimated_cost"] == "60.00"
    assert data["net_profit"] == "240.00"
    assert data["is_negative_margin"] is False


def test_simulacao_procedimento_inexistente_retorna_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    fake_id = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/sales/simulate",
        json={"procedure_id": fake_id},
        headers=auth_headers,
    )
    assert resp.status_code == 404
