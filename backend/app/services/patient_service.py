from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from app.core.phone import InvalidPhoneError, normalize_br_phone
from app.core.tz import today_in_timezone
from app.domain.messaging.templates import build_whatsapp_link
from app.domain.retention.enums import ReturnOpportunityStatus
from app.models.patient import Gender, Patient
from app.models.return_opportunity import ReturnOpportunity
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.schemas.patient import (
    PatientBatchImportError,
    PatientBatchImportItem,
    PatientBatchImportRequest,
    PatientBatchImportResult,
    PatientBirthdayOut,
    PatientCreate,
    PatientOut,
    PatientUpdate,
)


class PatientNotFoundError(Exception):
    pass


class PatientService:
    def __init__(
        self,
        repo: PatientRepository,
        procedure_repo: ProcedureRepository | None = None,
        return_opportunity_repo: ReturnOpportunityRepository | None = None,
        professional_repo: ProfessionalRepository | None = None,
    ) -> None:
        self._repo = repo
        self._procedures = procedure_repo
        self._return_opportunities = return_opportunity_repo
        self._professionals = professional_repo

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
            gender=dto.gender,
        )
        return self._repo.add(patient)

    def batch_import(
        self, request: PatientBatchImportRequest
    ) -> PatientBatchImportResult:
        """Importação em lote de pacientes com deduplicação por telefone e validação atômica (EPIC-S2-03, TASK-BACK-S2-14)."""
        existing_phones = self._repo.list_existing_phones()
        seen_batch_phones: set[str] = set()

        created_patient_pairs: list[tuple[Patient, PatientBatchImportItem]] = []
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
            created_patient_pairs.append((new_patient, item))

        # Transação atômica: se houver erros críticos (> 20% das linhas), aborta
        if total_items > 0 and len(errors) / total_items > 0.20:
            return PatientBatchImportResult(
                created_count=0,
                skipped_count=0,
                opportunities_created_count=0,
                errors=errors,
                patients=[],
            )

        for p, _ in created_patient_pairs:
            self._repo.add(p)

        # G-12: Gerar oportunidades de retorno retroativas (source=IMPORT)
        opportunities_created_count = 0
        if (
            (
                request.generate_return_opportunities
                or request.default_procedure_id is not None
            )
            and self._return_opportunities is not None
            and self._procedures is not None
        ):
            prof = (
                self._professionals.get_by_id(self._repo._professional_id)
                if self._professionals
                else None
            )
            tz = prof.timezone if prof and prof.timezone else "America/Sao_Paulo"
            today = today_in_timezone(tz)

            for p, item in created_patient_pairs:
                target_proc_id = item.procedure_id or request.default_procedure_id
                if not target_proc_id:
                    continue
                proc = self._procedures.get(target_proc_id)
                if not proc:
                    continue

                interval = proc.return_interval_days or 0
                if item.last_visit_date:
                    due_date = item.last_visit_date + timedelta(days=interval)
                else:
                    due_date = today

                opp = ReturnOpportunity(
                    patient_id=p.id,
                    procedure_id=proc.id,
                    source="IMPORT",
                    due_date=due_date,
                    status=ReturnOpportunityStatus.OPEN,
                )
                self._return_opportunities.add(opp)
                opportunities_created_count += 1

        self._repo.flush()

        return PatientBatchImportResult(
            created_count=len(created_patient_pairs),
            skipped_count=skipped_count,
            opportunities_created_count=opportunities_created_count,
            errors=errors,
            patients=[PatientOut.model_validate(p) for p, _ in created_patient_pairs],
        )

    def get(self, patient_id: UUID) -> Patient:
        patient = self._repo.get(patient_id)
        if patient is None:
            raise PatientNotFoundError()
        return patient

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        gender: Gender | None = None,
        has_upcoming_booking: bool | None = None,
        has_completed_treatment: bool | None = None,
    ) -> list[Patient]:
        return self._repo.list(
            limit=limit,
            offset=offset,
            search=search,
            gender=gender,
            has_upcoming_booking=has_upcoming_booking,
            has_completed_treatment=has_completed_treatment,
        )

    def count(
        self,
        *,
        search: str | None = None,
        gender: Gender | None = None,
        has_upcoming_booking: bool | None = None,
        has_completed_treatment: bool | None = None,
    ) -> int:
        return self._repo.count(
            search=search,
            gender=gender,
            has_upcoming_booking=has_upcoming_booking,
            has_completed_treatment=has_completed_treatment,
        )

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

    def list_birthdays(self, month: int | None = None) -> list[PatientBirthdayOut]:
        patients = self._repo.list_birthdays(month=month)
        today = today_in_timezone("America/Sao_Paulo")

        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]

        result: list[PatientBirthdayOut] = []
        for p in patients:
            if not p.birth_date:
                continue
            b_day = p.birth_date.day
            b_month = p.birth_date.month

            # Trata ano bissexto para 29 de fevereiro
            safe_day = 28 if b_month == 2 and b_day == 29 else b_day

            try:
                this_year_bday = date(today.year, b_month, safe_day)
            except ValueError:
                this_year_bday = date(today.year, b_month, 28)

            if this_year_bday < today:
                try:
                    next_bday = date(today.year + 1, b_month, safe_day)
                except ValueError:
                    next_bday = date(today.year + 1, b_month, 28)
            else:
                next_bday = this_year_bday

            days_until = (next_bday - today).days
            is_today = days_until == 0

            first_name = p.name.strip().split()[0] if p.name else ""
            wpp_msg = (
                f"Oi {first_name}! 🎉 Passando para te desejar um Feliz Aniversário! "
                f"Muita saúde, alegria e momentos especiais neste novo ciclo. "
                f"Para comemorar, preparamos um presente especial para você: "
                f"um mimo exclusivo no seu próximo procedimento este mês! Vamos agendar seu momento de autocuidado? ✨"
            )
            wpp_link = build_whatsapp_link(p.phone, wpp_msg) if p.phone else None

            result.append(
                PatientBirthdayOut(
                    patient_id=p.id,
                    patient_name=p.name,
                    patient_phone=p.phone,
                    birth_date=p.birth_date,
                    day=b_day,
                    month=b_month,
                    days_until=days_until,
                    is_today=is_today,
                    formatted_date=f"{b_day} de {meses[b_month - 1]}",
                    whatsapp_url=wpp_link,
                )
            )

        result.sort(key=lambda item: item.days_until)
        return result

