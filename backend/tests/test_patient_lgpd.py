from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.patient import Patient
from app.repositories.patient import PatientRepository
from app.services.patient_service import PatientService


def test_patient_anonymize() -> None:
    patient_id = uuid4()
    prof_id = uuid4()
    patient = Patient(
        id=patient_id,
        professional_id=prof_id,
        name="Maria da Silva",
        phone="11999998888",
        email="maria@teste.com",
        birth_date=date(1990, 5, 20),
        notes="Alergia a iodo",
        consent_whatsapp=True,
        is_active=True,
    )

    repo_mock = MagicMock(spec=PatientRepository)
    repo_mock.get.return_value = patient

    svc = PatientService(repo_mock)
    anonymized = svc.anonymize(patient_id)

    assert anonymized.name.startswith("Anonimizado_")
    assert anonymized.phone is None
    assert anonymized.email is None
    assert anonymized.notes is None
    assert anonymized.birth_date is None
    assert anonymized.consent_whatsapp is False
    assert anonymized.is_active is False
    assert anonymized.anonymized_at is not None
    repo_mock.flush.assert_called_once()


def test_patient_opt_out() -> None:
    patient_id = uuid4()
    prof_id = uuid4()
    patient = Patient(
        id=patient_id,
        professional_id=prof_id,
        name="Juliana Costa",
        phone="11988887777",
        consent_whatsapp=True,
        is_active=True,
    )

    repo_mock = MagicMock(spec=PatientRepository)
    repo_mock.get.return_value = patient

    svc = PatientService(repo_mock)
    updated = svc.opt_out(patient_id)

    assert updated.opted_out_at is not None
    assert updated.consent_whatsapp is False
    repo_mock.flush.assert_called_once()
