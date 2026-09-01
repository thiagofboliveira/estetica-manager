from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.bookings.enums import BookingStatus
from app.domain.bookings.state_machine import validate_booking_transition
from app.models.booking import Booking
from app.repositories.booking import BookingRepository
from app.repositories.patient import PatientRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.session import SessionRepository
from app.schemas.booking import BookingCreate, BookingUpdate


class BookingNotFoundError(Exception):
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

    def create(self, dto: BookingCreate) -> tuple[Booking, list[str]]:
        warnings: list[str] = []

        # Valida se há conflito de horário (aviso, sem bloqueio — MVP v7.1 §16.6, TASK-034b)
        session_conflicts = self._sessions.find_conflicts(dto.scheduled_at)
        booking_conflicts = self._bookings.find_conflicts(dto.scheduled_at)
        if session_conflicts or booking_conflicts:
            warnings.append(
                f"Aviso: Já existe atendimento agendado para o horário {dto.scheduled_at.isoformat()}."
            )

        booking = Booking(
            patient_id=dto.patient_id,
            patient_name_hint=dto.patient_name_hint,
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
        if dto.modality is not None:
            booking.modality = dto.modality
        if dto.note is not None:
            booking.note = dto.note

        self._bookings.flush()
        return booking, warnings
