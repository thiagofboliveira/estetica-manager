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
            PatientBatchImportItem(
                name="Juliana Duplicada", phone="(11) 98765-4321"
            ),  # existe na base -> skip
            PatientBatchImportItem(
                name="Carla Nova", phone="(21) 91234-5678"
            ),  # novo -> cria
            PatientBatchImportItem(
                name="Carla Repetida", phone="(21) 91234-5678"
            ),  # duplicado no lote -> skip
            PatientBatchImportItem(
                name="Sem Telefone", phone=None
            ),  # sem telefone -> cria
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
            PatientBatchImportItem(
                name="", phone=None
            ),  # erro (2/3 = 66% de erros > 20%)
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


def test_batch_import_generates_return_opportunities_with_source_import():
    """G-12: Importação pode gerar oportunidades de retorno retroativas com source=IMPORT."""
    from unittest.mock import MagicMock
    from uuid import uuid4

    from app.domain.retention.enums import ReturnOpportunityStatus

    mock_patient_repo = MagicMock()
    mock_patient_repo.list_existing_phones.return_value = set()
    mock_patient_repo._professional_id = uuid4()

    mock_proc_repo = MagicMock()
    proc_id = uuid4()
    mock_proc = MagicMock()
    mock_proc.id = proc_id
    mock_proc.return_interval_days = 45
    mock_proc_repo.get.return_value = mock_proc

    mock_opp_repo = MagicMock()
    mock_prof_repo = MagicMock()
    mock_prof = MagicMock()
    mock_prof.timezone = "America/Sao_Paulo"
    mock_prof_repo.get_by_id.return_value = mock_prof

    svc = PatientService(
        repo=mock_patient_repo,
        procedure_repo=mock_proc_repo,
        return_opportunity_repo=mock_opp_repo,
        professional_repo=mock_prof_repo,
    )

    req = PatientBatchImportRequest(
        patients=[
            PatientBatchImportItem(
                name="Paciente com Retorno 1", phone="(11) 91111-2222"
            ),
            PatientBatchImportItem(
                name="Paciente com Retorno 2", phone="(11) 93333-4444"
            ),
        ],
        default_procedure_id=proc_id,
        generate_return_opportunities=True,
    )

    res = svc.batch_import(req)

    assert res.created_count == 2
    assert res.opportunities_created_count == 2
    assert mock_opp_repo.add.call_count == 2

    # Verifica os atributos das oportunidades criadas
    created_opp = mock_opp_repo.add.call_args_list[0][0][0]
    assert created_opp.source == "IMPORT"
    assert created_opp.status == ReturnOpportunityStatus.OPEN
    assert created_opp.procedure_id == proc_id


@pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)
def test_import_integration_generates_retroactive_opportunities_not_attributed():
    """G-12 Integração: import gera oportunidade no Postgres com source=IMPORT e não entra em list_attributed."""
    import uuid
    from datetime import timedelta

    from app.core.rate_limit import InMemoryRateLimiter
    from app.db.session import get_tenant_session
    from app.models.return_opportunity import ReturnOpportunity
    from app.repositories.return_opportunity import ReturnOpportunityRepository

    # Isola o rate limiter para este teste
    deps._patient_import_rate_limiter = InMemoryRateLimiter(
        max_calls=10, window=timedelta(hours=1)
    )

    client = TestClient(app)
    login = client.post("/dev/login")
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 1. Cria procedimento
    proc_resp = client.post(
        "/api/v1/procedures",
        json={
            "name": f"Procedimento Retroativo {uuid.uuid4()}",
            "price": "350.00",
            "estimated_cost": "50.00",
            "return_interval_days": 60,
        },
        headers=headers,
    )
    assert proc_resp.status_code == 201, proc_resp.text
    proc_id = proc_resp.json()["id"]

    # 2. Importa paciente solicitando oportunidade retroativa
    unique_phone = f"(11) 9{uuid.uuid4().int % 100000000:08d}"
    import_resp = client.post(
        "/api/v1/patients/import",
        json={
            "patients": [
                {"name": f"Paciente G12 {uuid.uuid4()}", "phone": unique_phone}
            ],
            "default_procedure_id": proc_id,
            "generate_return_opportunities": True,
        },
        headers=headers,
    )
    assert import_resp.status_code == 200, import_resp.text
    data = import_resp.json()
    assert data["created_count"] == 1
    assert data["opportunities_created_count"] == 1
    patient_id = data["patients"][0]["id"]

    # 3. Verifica no banco real se o source foi persistido como "IMPORT"
    user_resp = client.get("/api/v1/users/me", headers=headers)
    prof_id = uuid.UUID(user_resp.json()["id"])
    gen = get_tenant_session(prof_id)
    session = next(gen)
    try:
        repo = ReturnOpportunityRepository(session, prof_id)
        opp = (
            session.query(ReturnOpportunity)
            .filter_by(patient_id=uuid.UUID(patient_id))
            .first()
        )
        assert opp is not None
        assert opp.source == "IMPORT"

        # 4. Prova que list_attributed exclui source=IMPORT (mesmo se contatada/resolvida)
        opp.contacted_at = opp.created_at
        session.flush()
        attributed = repo.list_attributed()
        assert not any(o.id == opp.id for o, _ in attributed)
    finally:
        import contextlib

        with contextlib.suppress(StopIteration):
            next(gen)
