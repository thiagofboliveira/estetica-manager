from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.patient import Patient
from app.repositories.patient import PatientRepository
from app.services.patient_service import PatientService


def test_list_birthdays():
    prof_id = uuid4()
    mock_repo = MagicMock(spec=PatientRepository)

    p1 = Patient(
        id=uuid4(),
        professional_id=prof_id,
        name="Camila Silva",
        phone="+5511999998888",
        birth_date=date(1995, 9, 15),
        is_active=True,
    )
    mock_repo.list_birthdays.return_value = [p1]

    svc = PatientService(repo=mock_repo)
    birthdays = svc.list_birthdays()

    assert len(birthdays) == 1
    item = birthdays[0]
    assert item.patient_name == "Camila Silva"
    assert item.day == 15
    assert item.month == 9
    assert item.whatsapp_url is not None
    assert "https://wa.me/5511999998888" in item.whatsapp_url
