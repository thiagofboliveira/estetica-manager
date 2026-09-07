"""Testes de integração para rastreamento de frascos de Botox e insumos perecíveis (US-03)."""

from decimal import Decimal
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


def test_create_and_consume_vial(client: TestClient, auth_headers: dict[str, str]):
    # 1. Abre um novo frasco de Botox de 100U
    resp_create = client.post(
        "/api/v1/vials",
        json={
            "medication_name": "Botox Allergan 100U",
            "lot_number": "LOT-2026-X",
            "total_units": "100.00",
            "cost_price": "850.00",
            "validity_days": 30,
            "notes": "Aberto na geladeira estética",
        },
        headers=auth_headers,
    )
    assert resp_create.status_code == 201, resp_create.text
    vial = resp_create.json()
    assert vial["medication_name"] == "Botox Allergan 100U"
    assert vial["total_units"] == "100.00"
    assert vial["used_units"] == "0.00"
    assert vial["remaining_units"] == "100.00"
    assert vial["cost_price"] == "850.00"
    assert vial["cost_per_unit"] == "8.50"
    assert vial["estimated_loss_risk"] == "850.00"
    assert vial["status"] == "OPEN"
    assert vial["is_expired"] is False
    assert vial["days_remaining"] >= 29

    vial_id = vial["id"]

    # 2. Lista frascos ativos
    resp_list = client.get("/api/v1/vials", headers=auth_headers)
    assert resp_list.status_code == 200
    active_ids = [v["id"] for v in resp_list.json()]
    assert vial_id in active_ids

    # 3. Consome 30 unidades em uma paciente
    resp_consume = client.post(
        f"/api/v1/vials/{vial_id}/consume",
        json={
            "units": "30.00",
            "notes": "Aplicação terço superior facial",
        },
        headers=auth_headers,
    )
    assert resp_consume.status_code == 200, resp_consume.text
    consumed_vial = resp_consume.json()
    assert consumed_vial["used_units"] == "30.00"
    assert consumed_vial["remaining_units"] == "70.00"
    assert consumed_vial["estimated_loss_risk"] == "595.00"  # 70 * 8.50
    assert consumed_vial["status"] == "OPEN"

    # 4. Tenta consumir mais do que resta (ex: 80U quando restam 70U)
    resp_invalid = client.post(
        f"/api/v1/vials/{vial_id}/consume",
        json={"units": "80.00"},
        headers=auth_headers,
    )
    assert resp_invalid.status_code == 400
    assert "excede o saldo" in resp_invalid.json()["detail"].lower()

    # 5. Consome as 70U restantes -> Frasco deve finalizar automaticamente
    resp_finish_consume = client.post(
        f"/api/v1/vials/{vial_id}/consume",
        json={"units": "70.00", "notes": "Segunda aplicação"},
        headers=auth_headers,
    )
    assert resp_finish_consume.status_code == 200
    finished_vial = resp_finish_consume.json()
    assert finished_vial["used_units"] == "100.00"
    assert finished_vial["remaining_units"] == "0.00"
    assert finished_vial["status"] == "FINISHED"

    # 6. Não deve mais aparecer na listagem de ativos padrão
    resp_active = client.get("/api/v1/vials", headers=auth_headers)
    assert resp_active.status_code == 200
    assert vial_id not in [v["id"] for v in resp_active.json()]

    # Mas deve aparecer com include_all=true
    resp_all = client.get("/api/v1/vials?include_all=true", headers=auth_headers)
    assert resp_all.status_code == 200
    assert vial_id in [v["id"] for v in resp_all.json()]
