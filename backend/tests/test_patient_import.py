from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.core.config import settings
from app.core.rate_limit import InMemoryRateLimiter
from app.main import app
from app.schemas.patient import (
    PatientBatchImportItem,
    PatientBatchImportRequest,
)
from app.services.patient_service import PatientService


def test_batch_import_happy_path():
    """Testa importação bem sucedida de múltiplos pacientes."""
    mock_repo = MagicMock()
    mock_repo.list_existing_phones.return_value = set()

    svc = PatientService(mock_repo)

    req = PatientBatchImportRequest(
        patients=[
            PatientBatchImportItem(name="Juliana Silva", phone="(11) 98765-4321"),
            PatientBatchImportItem(name="Carla Santos", phone="(21) 91234-5678"),
            PatientBatchImportItem(name="Beatriz Lima", phone=None),
        ]
    )

    res = svc.batch_import(req)

    assert res.created_count == 3
    assert res.skipped_count == 0
    assert len(res.errors) == 0
    assert len(res.patients) == 3
    assert mock_repo.add.call_count == 3
    mock_repo.flush.assert_called_once()


def test_batch_import_deduplicates_existing_and_in_batch():
    """Testa deduplicação contra a base existente e duplicatas dentro do mesmo lote."""
    mock_repo = MagicMock()
    # +5511987654321 já existe
    mock_repo.list_existing_phones.return_value = {"+5511987654321"}

    svc = PatientService(mock_repo)

    req = PatientBatchImportRequest(
        patients=[
            PatientBatchImportItem(name="Juliana Duplicada", phone="(11) 98765-4321"),  # existe na base -> skip
            PatientBatchImportItem(name="Carla Nova", phone="(21) 91234-5678"),         # novo -> cria
            PatientBatchImportItem(name="Carla Repetida", phone="(21) 91234-5678"),     # duplicado no lote -> skip
            PatientBatchImportItem(name="Sem Telefone", phone=None),                    # sem telefone -> cria
        ]
    )

    res = svc.batch_import(req)

    assert res.created_count == 2
    assert res.skipped_count == 2
    assert len(res.errors) == 0
    assert mock_repo.add.call_count == 2


def test_batch_import_atomic_rollback_on_high_error_rate():
    """Se mais de 20% das linhas contiverem erros críticos (ex: nome vazio), o lote é abortado."""
    mock_repo = MagicMock()
    mock_repo.list_existing_phones.return_value = set()

    svc = PatientService(mock_repo)

    req = PatientBatchImportRequest(
        patients=[
            PatientBatchImportItem(name="Valido 1", phone=None),
            PatientBatchImportItem(name="", phone=None),  # erro
            PatientBatchImportItem(name="", phone=None),  # erro (2/3 = 66% de erros > 20%)
        ]
    )

    res = svc.batch_import(req)

    assert res.created_count == 0
    assert len(res.errors) == 2
    assert mock_repo.add.call_count == 0


@pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)
def test_import_route_rate_limited_after_3_calls_per_hour():
    """A 4a chamada de POST /patients/import na mesma hora deve retornar 429 (AC-07)."""
    deps._patient_import_rate_limiter = InMemoryRateLimiter(
        max_calls=3, window=deps._patient_import_rate_limiter._window
    )

    client = TestClient(app)
    login = client.post("/dev/login")
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    payload = {"patients": [{"name": "Paciente Rate Limit", "phone": None}]}

    for _ in range(3):
        resp = client.post("/api/v1/patients/import", json=payload, headers=headers)
        assert resp.status_code == 200, resp.text

    resp = client.post("/api/v1/patients/import", json=payload, headers=headers)
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
