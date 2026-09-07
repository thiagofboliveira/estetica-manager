"""Testes de integração reais para a Galeria de Fotos Antes & Depois (US-01)."""

import uuid
from datetime import UTC, datetime

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


def _create_procedure(client: TestClient, headers: dict[str, str], name: str) -> str:
    payload = {"name": name, "price": "150.00", "estimated_cost": "40.00"}
    resp = client.post("/api/v1/procedures", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_create_and_list_patient_photos(client: TestClient, auth_headers: dict[str, str]):
    patient_id = _create_patient(client, auth_headers, f"Paciente Fotos {uuid.uuid4().hex[:6]}")
    proc_id = _create_procedure(client, auth_headers, f"Limpeza {uuid.uuid4().hex[:4]}")

    # Cria foto BEFORE
    resp_before = client.post(
        f"/api/v1/patients/{patient_id}/photos",
        json={
            "photo_type": "BEFORE",
            "procedure_id": proc_id,
            "image_url": "data:image/webp;base64,UklGRkAAAABXRUJQVlA4IDQAAADwAQCdASoBAAEAAQAcJaACdLoAAP7/2QAA",
            "caption": "Antes da primeira sessão",
            "authorized_social_media": True,
        },
        headers=auth_headers,
    )
    assert resp_before.status_code == 201, resp_before.text
    data_before = resp_before.json()
    assert data_before["photo_type"] == "BEFORE"
    assert data_before["patient_id"] == patient_id
    assert data_before["procedure_id"] == proc_id
    assert data_before["caption"] == "Antes da primeira sessão"
    assert data_before["authorized_social_media"] is True

    # Cria foto AFTER
    resp_after = client.post(
        f"/api/v1/patients/{patient_id}/photos",
        json={
            "photo_type": "AFTER",
            "procedure_id": proc_id,
            "image_url": "data:image/webp;base64,UklGRkAAAABXRUJQVlA4IDQAAADwAQCdASoBAAEAAQAcJaACdLoAAP7/2QAA",
            "caption": "Resultado após 15 dias",
            "authorized_social_media": False,
        },
        headers=auth_headers,
    )
    assert resp_after.status_code == 201
    data_after = resp_after.json()
    assert data_after["photo_type"] == "AFTER"

    # Listagem de todas as fotos da paciente
    list_resp = client.get(
        f"/api/v1/patients/{patient_id}/photos",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 2
    photo_ids = [p["id"] for p in items]
    assert data_before["id"] in photo_ids
    assert data_after["id"] in photo_ids

    # Filtro por tipo AFTER
    filter_resp = client.get(
        f"/api/v1/patients/{patient_id}/photos?photo_type=AFTER",
        headers=auth_headers,
    )
    assert filter_resp.status_code == 200
    after_items = filter_resp.json()
    assert all(p["photo_type"] == "AFTER" for p in after_items)
    assert data_after["id"] in [p["id"] for p in after_items]


def test_update_and_delete_photo(client: TestClient, auth_headers: dict[str, str]):
    patient_id = _create_patient(client, auth_headers, f"Paciente Update {uuid.uuid4().hex[:6]}")

    resp = client.post(
        f"/api/v1/patients/{patient_id}/photos",
        json={
            "photo_type": "GENERAL",
            "image_url": "data:image/webp;base64,testdata",
            "caption": "Foto inicial",
            "authorized_social_media": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    photo_id = resp.json()["id"]

    # Atualiza legenda e autorização LGPD
    patch_resp = client.patch(
        f"/api/v1/patients/{patient_id}/photos/{photo_id}",
        json={
            "caption": "Legenda atualizada com sucesso",
            "authorized_social_media": True,
            "photo_type": "BEFORE",
        },
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["caption"] == "Legenda atualizada com sucesso"
    assert updated["authorized_social_media"] is True
    assert updated["photo_type"] == "BEFORE"

    # Soft delete da foto
    del_resp = client.delete(
        f"/api/v1/patients/{patient_id}/photos/{photo_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 204

    # Não deve mais aparecer na listagem
    list_resp = client.get(
        f"/api/v1/patients/{patient_id}/photos",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    assert photo_id not in [p["id"] for p in list_resp.json()]


def test_patient_photos_validation_and_errors(client: TestClient, auth_headers: dict[str, str]):
    fake_patient = str(uuid.uuid4())
    resp = client.post(
        f"/api/v1/patients/{fake_patient}/photos",
        json={"image_url": "data:test", "photo_type": "BEFORE"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
