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

    def anonymize(self, patient_id: UUID) -> Patient:
        """Anonimização do paciente (LGPD Art. 18 VI + Art. 16 II, TASK-061).
        Preserva a integridade de vendas e sessões contábeis, mascarando
        todos os dados de identificação pessoal."""
        patient = self.get(patient_id)
        patient.name = f"Anonimizado_{str(patient_id)[:8]}"
        patient.phone = None
        patient.email = None
        patient.notes = None
        patient.birth_date = None
        patient.consent_whatsapp = False
        patient.anonymized_at = datetime.now(UTC)
        patient.is_active = False
        self._repo.flush()
        return patient

    def opt_out(self, patient_id: UUID) -> Patient:
        """Registra opt-out de mensagens/WhatsApp (TASK-060, LGPD Art. 11)."""
        patient = self.get(patient_id)
        patient.opted_out_at = datetime.now(UTC)
        patient.consent_whatsapp = False
        self._repo.flush()
        return patient

    def export_data(self, patient_id: UUID) -> dict:
        """Exportação estruturada de dados do titular para portabilidade (LGPD Art. 18, V, TASK-062)."""
        patient = self.get(patient_id)
        return {
            "id": str(patient.id),
            "name": patient.name,
            "phone": patient.phone,
            "email": patient.email,
            "birth_date": patient.birth_date.isoformat()
            if patient.birth_date
            else None,
            "notes": patient.notes,
            "consent_whatsapp": patient.consent_whatsapp,
            "consent_at": patient.consent_at.isoformat()
            if patient.consent_at
            else None,
            "opted_out_at": patient.opted_out_at.isoformat()
            if patient.opted_out_at
            else None,
            "anonymized_at": patient.anonymized_at.isoformat()
            if patient.anonymized_at
            else None,
            "is_active": patient.is_active,
            "created_at": patient.created_at.isoformat()
            if patient.created_at
            else None,
            "updated_at": patient.updated_at.isoformat()
            if patient.updated_at
            else None,
        }
