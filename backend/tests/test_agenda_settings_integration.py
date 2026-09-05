"""Épico A — "Modo Ocupado": configuração de janela de trabalho em
financial_settings. Teste de integração REAL contra o Postgres do
Docker (mesmo padrão de tests/test_sales_integration.py).
"""

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


def test_get_traz_defaults_de_janela_de_trabalho(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    resp = client.get("/api/v1/financial-settings", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["work_start_time"] is not None
    assert body["work_end_time"] is not None
    assert body["slot_duration_minutes"] > 0
    assert body["buffer_minutes"] >= 0


def test_patch_atualiza_janela_de_trabalho(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original = client.get("/api/v1/financial-settings", headers=auth_headers).json()

    patch = client.patch(
        "/api/v1/financial-settings",
        json={
            "work_start_time": "09:00:00",
            "work_end_time": "17:00:00",
            "slot_duration_minutes": 45,
            "buffer_minutes": 10,
        },
        headers=auth_headers,
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body["work_start_time"] == "09:00:00"
    assert body["work_end_time"] == "17:00:00"
    assert body["slot_duration_minutes"] == 45
    assert body["buffer_minutes"] == 10

    # Restaura pra não sujar outros testes/ambiente de dev.
    client.patch(
        "/api/v1/financial-settings",
        json={
            "work_start_time": original["work_start_time"],
            "work_end_time": original["work_end_time"],
            "slot_duration_minutes": original["slot_duration_minutes"],
            "buffer_minutes": original["buffer_minutes"],
        },
        headers=auth_headers,
    )
