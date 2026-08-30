from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.patient import Patient
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.services.patient_service import PatientNotFoundError, PatientService
from app.services.procedure_service import ProcedureNotFoundError, ProcedureService


def test_patient_service_tenant_isolation_raises_404():
    """T-046: Acessar paciente que não existe no tenant da profissional levanta
    PatientNotFoundError (que vira 404, nunca 403 para não vazar existência)."""
    patient_id = uuid4()

    repo_mock = MagicMock(spec=PatientRepository)
    repo_mock.get.return_value = None  # Não encontrado no tenant A

    svc = PatientService(repo_mock)

    with pytest.raises(PatientNotFoundError):
        svc.get(patient_id)

    with pytest.raises(PatientNotFoundError):
        svc.archive(patient_id)

    with pytest.raises(PatientNotFoundError):
        svc.anonymize(patient_id)


def test_procedure_service_tenant_isolation_raises_404():
    """T-046: Acessar procedimento de outro tenant levanta ProcedureNotFoundError."""
    repo_mock = MagicMock(spec=ProcedureRepository)
    repo_mock.get.return_value = None

    svc = ProcedureService(repo_mock)

    with pytest.raises(ProcedureNotFoundError):
        svc.get(uuid4())

    with pytest.raises(ProcedureNotFoundError):
        svc.deactivate(uuid4())


def test_tenant_repository_always_assigns_professional_id():
    """T-046a: TenantRepository.add() sempre carimba o professional_id da sessão quando None."""
    tenant_id = uuid4()
    session_mock = MagicMock()

    repo = PatientRepository(session_mock, tenant_id)
    patient = Patient(name="Teste", professional_id=None)

    added = repo.add(patient)
    assert added.professional_id == tenant_id


def test_tenant_repository_blocks_cross_tenant_assignment():
    """T-046a: Tentativa de gravar objeto com outro professional_id levanta ValueError."""
    tenant_id = uuid4()
    hacker_tenant_id = uuid4()
    session_mock = MagicMock()

    repo = PatientRepository(session_mock, tenant_id)
    patient = Patient(name="Teste", professional_id=hacker_tenant_id)

    with pytest.raises(ValueError, match="tentativa de gravar em tenant alheio"):
        repo.add(patient)
