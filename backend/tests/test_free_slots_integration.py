"""Épico A — "Modo Ocupado": GET /free-slots. Teste de integração REAL
contra o Postgres do Docker (mesmo padrão de tests/test_sales_integration.py).
"""

import uuid
from datetime import date, timedelta

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


def test_dia_sem_compromissos_retorna_slots_da_janela_configurada(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original = client.get("/api/v1/financial-settings", headers=auth_headers).json()
    client.patch(
        "/api/v1/financial-settings",
        json={
            "work_start_time": "08:00:00",
            "work_end_time": "09:00:00",
            "slot_duration_minutes": 30,
            "buffer_minutes": 0,
        },
        headers=auth_headers,
    )

    try:
        # Uma data futura distante o suficiente pra não colidir com
        # bookings/sessions criados por outros testes de integração.
        resp = client.get(
            "/api/v1/free-slots",
            params={"date": "2031-01-15"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["slots"] == ["08:00:00", "08:30:00"]
        assert body["message"] == (
            "Oi! Tenho horário livre hoje às 8h e 8h30. Qual fica melhor pra você?"
        )
    finally:
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


def test_booking_no_dia_remove_o_slot_correspondente(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original = client.get("/api/v1/financial-settings", headers=auth_headers).json()
    client.patch(
        "/api/v1/financial-settings",
        json={
            "work_start_time": "08:00:00",
            "work_end_time": "09:00:00",
            "slot_duration_minutes": 30,
            "buffer_minutes": 0,
        },
        headers=auth_headers,
    )

    # Dia aleatório dentro de uma janela futura ampla: evita colisão com
    # bookings residuais de execuções anteriores deste mesmo teste no
    # ambiente de dev compartilhado (que não faz cleanup do booking).
    day_offset = uuid.uuid4().int % 3650
    target_date = (date(2030, 1, 1) + timedelta(days=day_offset)).isoformat()

    try:
        booking = client.post(
            "/api/v1/bookings",
            json={
                "patient_name_hint": f"Lead Teste {uuid.uuid4()}",
                "scheduled_at": f"{target_date}T08:00:00-03:00",
            },
            headers=auth_headers,
        )
        assert booking.status_code == 201, booking.text

        resp = client.get(
            "/api/v1/free-slots",
            params={"date": target_date},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["slots"] == ["08:30:00"]
    finally:
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
