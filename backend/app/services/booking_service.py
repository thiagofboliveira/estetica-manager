from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from app.core.phone import InvalidPhoneError, normalize_br_phone
from app.domain.bookings.enums import BookingStatus
from app.domain.bookings.state_machine import validate_booking_transition
from app.models.booking import Booking
from app.models.patient import Patient
from app.repositories.booking import BookingRepository
from app.repositories.patient import PatientRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.session import SessionRepository
from app.schemas.booking import BookingCreate, BookingUpdate


class BookingNotFoundError(Exception):
    pass


class BookingConflictError(Exception):
    pass


class BookingInvalidStateError(Exception):
    pass


class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        session_repo: SessionRepository,
        patient_repo: PatientRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._bookings = booking_repo
        self._sessions = session_repo
        self._patients = patient_repo
        self._professionals = professional_repo

    def get(self, booking_id: UUID) -> Booking:
        booking = self._bookings.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundError()
        return booking

    def get_by_token(self, booking_id: UUID, token: str) -> Booking:
        booking = self._bookings.get_by_id_and_token(booking_id, token)
        if booking is None:
            raise BookingNotFoundError()
        return booking

    def create(self, dto: BookingCreate) -> tuple[Booking, list[str]]:
        warnings: list[str] = []

        # Valida se há conflito de horário (aviso, sem bloqueio — MVP v7.1 §16.6, TASK-034b)
        session_conflicts = self._sessions.find_conflicts(dto.scheduled_at)
        booking_conflicts = self._bookings.find_conflicts(dto.scheduled_at)
        if session_conflicts or booking_conflicts:
            warnings.append(
                f"Aviso: Já existe atendimento agendado para o horário {dto.scheduled_at.isoformat()}."
            )

        patient_id = dto.patient_id
        patient_name_hint = dto.patient_name_hint
        patient_phone = dto.patient_phone

        # Se não informou patient_id mas informou telefone, tenta associar ou registrar
        if not patient_id and patient_phone:
            # Normaliza antes de buscar: um paciente cadastrado via tela
            # (PatientService.create) já está em E.164. Comparar a string
            # crua vinda do link público duplicava a paciente sempre que o
            # formato divergia (com/sem +55, DDD sem o 9).
            try:
                lookup_phone = normalize_br_phone(patient_phone)
            except InvalidPhoneError:
                lookup_phone = patient_phone.strip()
            existing = self._patients.get_by_phone(lookup_phone)
            if existing:
                patient_id = existing.id
                if not patient_name_hint:
                    patient_name_hint = existing.name
                # A-02: consentimento só sobe (False->True), nunca desce
                # aqui — retirar consentimento é ato explícito em
                # PatientService.update, não efeito colateral de agendar.
                if dto.patient_consent_whatsapp and not existing.consent_whatsapp:
                    existing.consent_whatsapp = True
                    existing.consent_at = datetime.now(UTC)
            elif patient_name_hint:
                # Cria novo paciente automaticamente no tenant
                new_patient = Patient(
                    name=patient_name_hint.strip(),
                    phone=lookup_phone,
                    is_active=True,
                    consent_whatsapp=dto.patient_consent_whatsapp,
                    consent_at=(
                        datetime.now(UTC) if dto.patient_consent_whatsapp else None
                    ),
                )
                created_p = self._patients.add(new_patient)
                self._patients.flush()
                patient_id = created_p.id

        booking = Booking(
            patient_id=patient_id,
            patient_name_hint=patient_name_hint,
            patient_phone=patient_phone,
            procedure_id=dto.procedure_id,
            scheduled_at=dto.scheduled_at,
            modality=dto.modality,
            note=dto.note,
            status=BookingStatus.SCHEDULED,
        )
        booking = self._bookings.add(booking)
        self._bookings.flush()
        return booking, warnings

    def list_bookings(
        self, from_date: date | None = None, to_date: date | None = None
    ) -> list[Booking]:
        if from_date and to_date:
            prof = self._professionals.get_by_id(self._bookings._professional_id)
            tz_name = prof.timezone if prof and prof.timezone else "America/Sao_Paulo"
            tz = ZoneInfo(tz_name)
            start_dt = datetime.combine(from_date, time.min).replace(tzinfo=tz)
            end_dt = datetime.combine(to_date, time.max).replace(tzinfo=tz)
            return self._bookings.list_in_range(start_dt, end_dt)
        return self._bookings.list_in_range(
            datetime.min.replace(tzinfo=UTC), datetime.max.replace(tzinfo=UTC)
        )

    def update(self, booking_id: UUID, dto: BookingUpdate) -> tuple[Booking, list[str]]:
        booking = self.get(booking_id)
        warnings: list[str] = []

        if dto.scheduled_at is not None:
            session_conflicts = self._sessions.find_conflicts(dto.scheduled_at)
            booking_conflicts = self._bookings.find_conflicts(
                dto.scheduled_at, exclude_booking_id=booking.id
            )
            if session_conflicts or booking_conflicts:
                warnings.append(
                    f"Aviso: Já existe atendimento agendado para o horário {dto.scheduled_at.isoformat()}."
                )
            booking.scheduled_at = dto.scheduled_at

        if dto.status is not None and dto.status != booking.status:
            validate_booking_transition(booking.status, dto.status)
            booking.status = dto.status

        if dto.patient_id is not None:
            booking.patient_id = dto.patient_id
        if dto.patient_name_hint is not None:
            booking.patient_name_hint = dto.patient_name_hint
        if dto.patient_phone is not None:
            booking.patient_phone = dto.patient_phone
        if dto.procedure_id is not None:
            booking.procedure_id = dto.procedure_id
        if dto.modality is not None:
            booking.modality = dto.modality
        if dto.note is not None:
            booking.note = dto.note

        self._bookings.flush()
        return booking, warnings

    def reschedule_by_token(
        self,
        booking_id: UUID,
        token: str,
        new_time: datetime | None,
        new_procedure_id: UUID | None,
        note: str | None,
    ) -> Booking:
        booking = self.get_by_token(booking_id, token)

        if booking.status != BookingStatus.SCHEDULED:
            raise BookingInvalidStateError(
                f"Agendamento não pode ser alterado no status atual: {booking.status.value}"
            )

        if new_time is not None:
            # Não permite remarcar para o passado
            if new_time <= datetime.now(UTC):
                raise ValueError("O novo horário deve ser no futuro.")

            # Bloqueio estrito de conflito para remarcação pública
            session_conflicts = self._sessions.find_conflicts(new_time)
            booking_conflicts = self._bookings.find_conflicts(
                new_time, exclude_booking_id=booking.id
            )
            if session_conflicts or booking_conflicts:
                raise BookingConflictError("Este horário já está ocupado.")

            booking.scheduled_at = new_time

        if new_procedure_id is not None:
            booking.procedure_id = new_procedure_id

        if note is not None:
            booking.note = note

        self._bookings.flush()
        return booking

    def cancel_by_token(self, booking_id: UUID, token: str) -> Booking:
        booking = self.get_by_token(booking_id, token)

        if booking.status == BookingStatus.CANCELLED:
            return booking

        if booking.status != BookingStatus.SCHEDULED:
            raise BookingInvalidStateError(
                f"Agendamento não pode ser cancelado no status atual: {booking.status.value}"
            )

        validate_booking_transition(booking.status, BookingStatus.CANCELLED)
        booking.status = BookingStatus.CANCELLED
        self._bookings.flush()
        return booking

    def confirm(self, booking_id: UUID) -> Booking:
        """Registra a confirmação de presença do booking público (anti-no-show)."""
        booking = self.get(booking_id)
        if booking.confirmed_at is not None:
            return booking  # idempotente
        booking.confirmed_at = datetime.now(UTC)
        self._bookings.flush()
        return booking
