from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.phone import InvalidPhoneError, normalize_br_phone
from app.models.patient import Patient
from app.repositories.patient import PatientRepository
from app.schemas.patient import (
    PatientBatchImportError,
    PatientBatchImportRequest,
    PatientBatchImportResult,
    PatientCreate,
    PatientOut,
    PatientUpdate,
)


class PatientNotFoundError(Exception):
    pass


class PatientService:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    def create(self, dto: PatientCreate) -> Patient:
        phone = normalize_br_phone(dto.phone) if dto.phone else None
        consent_at = datetime.now(UTC) if dto.consent_whatsapp else None
        patient = Patient(
            name=dto.name,
            phone=phone,
            email=dto.email,
            birth_date=dto.birth_date,
            notes=dto.notes,
            consent_whatsapp=dto.consent_whatsapp,
            consent_at=consent_at,
        )
        return self._repo.add(patient)

    def batch_import(self, request: PatientBatchImportRequest) -> PatientBatchImportResult:
        """Importação em lote de pacientes com deduplicação por telefone e validação atômica (EPIC-S2-03, TASK-BACK-S2-14)."""
        existing_phones = self._repo.list_existing_phones()
        seen_batch_phones: set[str] = set()

        created_patients: list[Patient] = []
        errors: list[PatientBatchImportError] = []
        skipped_count = 0

        total_items = len(request.patients)

        for i, item in enumerate(request.patients):
            line_no = i + 1
            name = item.name.strip() if item.name else ""

            if not name:
                errors.append(
                    PatientBatchImportError(line=line_no, reason="Nome é obrigatório.")
                )
                continue

            normalized_phone: str | None = None
            if item.phone and item.phone.strip():
                try:
                    normalized_phone = normalize_br_phone(item.phone)
                except (InvalidPhoneError, ValueError):
                    # Validação suave: telefone malformado vira None com aviso
                    normalized_phone = None

            # Deduplicação: se telefone já existe no tenant ou neste lote, pula
            if normalized_phone:
                if (
                    normalized_phone in existing_phones
                    or normalized_phone in seen_batch_phones
                ):
                    skipped_count += 1
                    continue
                seen_batch_phones.add(normalized_phone)

            now = datetime.now(UTC)
            new_patient = Patient(
                id=uuid4(),
                name=name,
                phone=normalized_phone,
                email=item.email.strip() if item.email else None,
                notes=item.notes,
                consent_whatsapp=False,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            created_patients.append(new_patient)

        # Transação atômica: se houver erros críticos (> 20% das linhas), aborta
        if total_items > 0 and len(errors) / total_items > 0.20:
            return PatientBatchImportResult(
                created_count=0,
                skipped_count=0,
                errors=errors,
                patients=[],
            )

        for p in created_patients:
            self._repo.add(p)

        self._repo.flush()

        return PatientBatchImportResult(
            created_count=len(created_patients),
            skipped_count=skipped_count,
            errors=errors,
            patients=[PatientOut.model_validate(p) for p in created_patients],
        )

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
