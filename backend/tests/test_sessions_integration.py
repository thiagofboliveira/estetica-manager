"""T-016 — PATCH /sessions/{id}. Testado contra Postgres real, mesmo
padrão de test_sales_integration.py."""

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
def token(client: TestClient) -> str:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient_id(client, auth_headers):
    resp = client.post(
        "/api/v1/patients", json={"name": "Paciente Sessão"}, headers=auth_headers
    )
    return resp.json()["id"]


@pytest.fixture
def procedure_id(client, auth_headers):
    resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Procedimento Sessão",
            "price": "100.00",
            "estimated_cost": "10.00",
            "return_interval_days": 30,
        },
        headers=auth_headers,
    )
    return resp.json()["id"]


def test_patch_session_para_completed_seta_completed_at(
    client, auth_headers, patient_id, procedure_id
):
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    session_id = sale_resp.json()["sessions"][0]["id"]

    resp = client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None


def test_patch_session_transicao_invalida_retorna_409(
    client, auth_headers, patient_id, procedure_id
):
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    session_id = sale_resp.json()["sessions"][0]["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )

    resp = client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "SCHEDULED"},
        headers=auth_headers,
    )

    assert resp.status_code == 409


def test_patch_session_inexistente_retorna_404(client, auth_headers):
    resp = client.patch(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000000",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
