from datetime import UTC, datetime
from uuid import UUID

from app.core.phone import normalize_br_phone
from app.models.patient import Patient
from app.repositories.patient import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientNotFoundError(Exception):
    pass


class PatientService:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    def create(self, dto: PatientCreate) -> Patient:
        phone = normalize_br_phone(dto.phone) if dto.phone else None
        patient = Patient(
            name=dto.name,
            phone=phone,
            email=dto.email,
            birth_date=dto.birth_date,
            notes=dto.notes,
        )
        return self._repo.add(patient)

    def get(self, patient_id: UUID) -> Patient:
        patient = self._repo.get(patient_id)
        if patient is None:
            raise PatientNotFoundError()
        return patient

    def list(
        self, *, limit: int = 50, offset: int = 0, search: str | None = None
    ) -> list[Patient]:
        return self._repo.list(limit=limit, offset=offset, search=search)

    def update(self, patient_id: UUID, dto: PatientUpdate) -> Patient:
        patient = self.get(patient_id)
        data = dto.model_dump(exclude_unset=True)

        consenting = data.pop("consent_whatsapp", None)
        if consenting is True and not patient.consent_whatsapp:
            patient.consent_at = datetime.now(UTC)
        patient.consent_whatsapp = (
            consenting if consenting is not None else patient.consent_whatsapp
        )

        if "phone" in data and data["phone"]:
            data["phone"] = normalize_br_phone(data["phone"])

        for field, value in data.items():
            setattr(patient, field, value)

        self._repo.flush()
        return patient

    def archive(self, patient_id: UUID) -> None:
        """DELETE = arquivar (is_active=False), nunca hard delete
        (MVP v6 §10 — concilia LGPD com retenção fiscal)."""
        patient = self.get(patient_id)
        patient.is_active = False
        self._repo.flush()
