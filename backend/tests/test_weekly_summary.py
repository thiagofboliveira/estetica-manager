"""Testes de integração para o resumo semanal e descadastro em 1 clique (A-12 / V5-01 / V5-02)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.weekly_summary_service import calculate_last_week_bounds

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


def test_calculate_last_week_bounds() -> None:
    # 2026-09-07 é uma Segunda-feira (weekday 0)
    # A semana passada foi de 2026-08-31 a 2026-09-06
    segunda = date(2026, 9, 7)
    inicio, fim = calculate_last_week_bounds(segunda)
    assert inicio == date(2026, 8, 31)
    assert fim == date(2026, 9, 6)

    # 2026-09-10 é uma Quinta-feira (weekday 3)
    # A semana passada continua sendo de 2026-08-31 a 2026-09-06
    quinta = date(2026, 9, 10)
    inicio2, fim2 = calculate_last_week_bounds(quinta)
    assert inicio2 == date(2026, 8, 31)
    assert fim2 == date(2026, 9, 6)


def test_get_weekly_summary_endpoint(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Garante que começa ativo
    client.patch(
        "/api/v1/weekly-summary/settings",
        json={"weekly_summary_enabled": True},
        headers=auth_headers,
    )
    resp = client.get("/api/v1/weekly-summary", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "professional_name" in data
    assert "period_start" in data
    assert "period_end" in data
    assert "gross_revenue" in data
    assert "net_profit" in data
    assert "sales_count" in data
    assert "pending_opportunities_count" in data
    assert "whatsapp_message" in data
    assert "unsubscribe_url" in data
    assert "Resumo da Semana" in data["whatsapp_message"]
    assert data["weekly_summary_enabled"] is True


def test_weekly_summary_with_real_sale(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Cria paciente e procedimento
    pat_resp = client.post(
        "/api/v1/patients",
        json={"name": f"Paciente Resumo {uuid.uuid4().hex[:6]}", "phone": "11999998888"},
        headers=auth_headers,
    )
    assert pat_resp.status_code == 201
    pat_id = pat_resp.json()["id"]

    proc_resp = client.post(
        "/api/v1/procedures",
        json={"name": f"Proc Resumo {uuid.uuid4().hex[:6]}", "price": "250.00", "estimated_cost": "50.00"},
        headers=auth_headers,
    )
    assert proc_resp.status_code == 201
    proc_id = proc_resp.json()["id"]

    # Cria venda na semana corrente
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": pat_id,
            "type": "SINGLE",
            "payment_method": "PIX",
            "items": [{"procedure_id": proc_id, "quantity": 1}],
        },
        headers=auth_headers,
    )
    assert sale_resp.status_code == 201, sale_resp.text

    # Busca resumo da semana corrente
    resp = client.get("/api/v1/weekly-summary", params={"use_current_week": True}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["gross_revenue"]) >= Decimal("250.00")
    assert Decimal(data["net_profit"]) > Decimal("0.00")
    assert data["sales_count"] >= 1


def test_weekly_summary_settings_toggle(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Desativa
    resp = client.patch(
        "/api/v1/weekly-summary/settings",
        json={"weekly_summary_enabled": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["weekly_summary_enabled"] is False

    # Reativa
    resp2 = client.patch(
        "/api/v1/weekly-summary/settings",
        json={"weekly_summary_enabled": True},
        headers=auth_headers,
    )
    assert resp2.status_code == 200
    assert resp2.json()["weekly_summary_enabled"] is True


def test_public_1click_unsubscribe(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Obtem a URL com o token da profissional autenticada
    summary_resp = client.get("/api/v1/weekly-summary", headers=auth_headers)
    assert summary_resp.status_code == 200
    unsub_url = summary_resp.json()["unsubscribe_url"]
    token = unsub_url.split("token=")[-1]
    assert len(token) >= 20

    # Faz o descadastro público com 1 clique (sem header de auth!)
    unsub_resp = client.get(
        "/api/v1/public/weekly-summary/unsubscribe",
        params={"token": token},
        headers={"Accept": "application/json"},
    )
    assert unsub_resp.status_code == 200
    assert unsub_resp.json()["status"] == "unsubscribed"

    # Confirma que a profissional agora está com weekly_summary_enabled = False
    check_resp = client.get("/api/v1/weekly-summary", headers=auth_headers)
    assert check_resp.status_code == 200
    assert check_resp.json()["weekly_summary_enabled"] is False

    # Testa também resposta HTML
    html_resp = client.get(
        "/api/v1/public/weekly-summary/unsubscribe",
        params={"token": token},
        headers={"Accept": "text/html"},
    )
    assert html_resp.status_code == 200
    assert "Resumo semanal pausado" in html_resp.text


def test_public_unsubscribe_invalid_token_retorna_404(client: TestClient) -> None:
    fake_token = "invalid-token-" + uuid.uuid4().hex
    resp = client.get(
        "/api/v1/public/weekly-summary/unsubscribe",
        params={"token": fake_token},
    )
    assert resp.status_code == 404
