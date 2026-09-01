from unittest.mock import MagicMock

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
