"""Public Agenda & Booking API — Links públicos para agendamento na bio e WhatsApp.

Permite que pacientes visualizem procedimentos, horários livres e criem reservas
sem necessidade de autenticação (zero atrito). Todas as operações de agendamento
geram um `management_token` seguro para consulta, remarcação e cancelamento pela paciente.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select

from app.core.rate_limit import InMemoryRateLimiter
from app.db.session import tenant_session, unsafe_session_without_tenant
from app.models.booking import Booking
from app.models.procedure import Procedure, ProcedureType
from app.models.professional import Professional
from app.repositories.booking import BookingRepository
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.schemas.booking import (
    BookingCreate,
    PublicBookingCreate,
    PublicBookingOut,
    PublicBookingReschedule,
    PublicProcedureOut,
    PublicProfessionalInfo,
)
from app.services.agenda_service import AgendaService
from app.services.booking_service import (
    BookingConflictError,
    BookingInvalidStateError,
    BookingService,
)
from app.services.financial_settings_service import FinancialSettingsService
from app.services.session_service import SessionService

router = APIRouter(prefix="/public", tags=["public-agenda"])

# Rate limiters por IP para proteção anti-abuso/DDoS
_booking_rate_limiter = InMemoryRateLimiter(max_calls=20, window=timedelta(hours=1))
_query_rate_limiter = InMemoryRateLimiter(max_calls=120, window=timedelta(hours=1))


def check_public_booking_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    retry_after = _booking_rate_limiter.check(client_ip)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas solicitações de agendamento. Tente novamente mais tarde.",
            headers={"Retry-After": str(max(1, int(retry_after.total_seconds())))},
        )


def check_public_query_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    retry_after = _query_rate_limiter.check(client_ip)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas consultas realizadas. Aguarde um instante.",
            headers={"Retry-After": str(max(1, int(retry_after.total_seconds())))},
        )


PublicBookingRateLimit = Annotated[None, Depends(check_public_booking_limit)]
PublicQueryRateLimit = Annotated[None, Depends(check_public_query_limit)]


def _resolve_slug(slug: str) -> tuple[UUID, str, str | None, str]:
    """Resolve o slug desautenticado na tabela professionals via bypass_tenant restrito."""
    clean_slug = slug.strip().lower()
    with unsafe_session_without_tenant("lookup public agenda slug") as sys_sess:
        stmt = select(
            Professional.id,
            Professional.name,
            Professional.bio,
            Professional.slug,
        ).where(
            Professional.slug == clean_slug,
            Professional.is_active.is_(True),
        )
        row = sys_sess.execute(stmt).first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agenda não encontrada para este link.",
            )
        return row[0], row[1], row[2], row[3]


def _resolve_booking_tenant(booking_id: UUID, token: str) -> tuple[UUID, UUID]:
    """Descobre o tenant dono do agendamento validando simultaneamente id e token."""
    with unsafe_session_without_tenant("lookup booking tenant by token") as sys_sess:
        stmt = select(Booking.professional_id).where(
            Booking.id == booking_id,
            Booking.management_token == token.strip(),
        )
        prof_id = sys_sess.scalar(stmt)
        if not prof_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado ou link de acesso inválido.",
            )
        return booking_id, prof_id


def _build_booking_service(session, professional_id: UUID) -> BookingService:
    return BookingService(
        booking_repo=BookingRepository(session, professional_id),
        session_repo=SessionRepository(session, professional_id),
        patient_repo=PatientRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def _build_agenda_service(session, professional_id: UUID) -> AgendaService:
    session_repo = SessionRepository(session, professional_id)
    sale_item_repo = SaleItemRepository(session, professional_id)
    sale_repo = SaleRepository(session, professional_id)
    procedure_repo = ProcedureRepository(session, professional_id)
    patient_repo = PatientRepository(session, professional_id)
    booking_repo = BookingRepository(session, professional_id)
    return_opp_repo = ReturnOpportunityRepository(session, professional_id)
    prof_repo = ProfessionalRepository(session, professional_id)
    financial_settings_repo = FinancialSettingsRepository(session, professional_id)

    session_svc = SessionService(
        session_repo=session_repo,
        sale_item_repo=sale_item_repo,
        sale_repo=sale_repo,
        procedure_repo=procedure_repo,
        patient_repo=patient_repo,
        booking_repo=booking_repo,
        return_opportunity_repo=return_opp_repo,
        professional_repo=prof_repo,
    )
    fin_svc = FinancialSettingsService(financial_settings_repo)
    return AgendaService(
        session_service=session_svc,
        financial_settings_service=fin_svc,
        professional_repo=prof_repo,
    )


@router.get("/agenda/{slug}", response_model=PublicProfessionalInfo)
def get_public_agenda_profile(
    slug: str, _rate_limit: PublicQueryRateLimit
) -> PublicProfessionalInfo:
    """Retorna dados públicos da profissional e a lista de procedimentos disponíveis."""
    prof_id, prof_name, prof_bio, prof_slug = _resolve_slug(slug)

    with tenant_session(prof_id) as session:
        proc_repo = ProcedureRepository(session, prof_id)
        # Lista somente serviços ativos
        stmt = (
            proc_repo._scoped()
            .where(
                Procedure.is_active.is_(True), Procedure.type == ProcedureType.SERVICE
            )
            .order_by(Procedure.name.asc())
        )
        procedures = list(session.scalars(stmt))

        proc_out = [
            PublicProcedureOut(
                id=p.id,
                name=p.name,
                price=p.price,
                return_interval_days=p.return_interval_days,
                session_plan=p.session_plan.value,
            )
            for p in procedures
        ]

        return PublicProfessionalInfo(
            name=prof_name,
            slug=prof_slug,
            bio=prof_bio,
            procedures=proc_out,
        )


@router.get("/agenda/{slug}/slots", response_model=list[str])
def get_public_slots(
    slug: str,
    target_date: date = Query(..., alias="date"),
    _rate_limit: PublicQueryRateLimit = None,
) -> list[str]:
    """Retorna horários disponíveis no dia para agendamento público."""
    if target_date < date.today():
        return []

    prof_id, _, _, _ = _resolve_slug(slug)

    with tenant_session(prof_id) as session:
        agenda_svc = _build_agenda_service(session, prof_id)
        slots, _ = agenda_svc.get_free_slots(target_date)
        return [s.strftime("%H:%M") for s in slots]


@router.post(
    "/agenda/{slug}/bookings",
    response_model=PublicBookingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_public_booking(
    slug: str,
    body: PublicBookingCreate,
    _rate_limit: PublicBookingRateLimit,
) -> PublicBookingOut:
    """Cria um agendamento público sem necessidade de senha para o paciente."""
    if body.scheduled_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O horário de agendamento deve ser futuro.",
        )

    prof_id, prof_name, _, prof_slug = _resolve_slug(slug)

    with tenant_session(prof_id) as session:
        # Valida se o procedimento existe e está ativo
        proc_repo = ProcedureRepository(session, prof_id)
        proc = proc_repo.get(body.procedure_id)
        if not proc or not proc.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Procedimento selecionado não encontrado ou inativo.",
            )

        booking_svc = _build_booking_service(session, prof_id)

        # Checa conflito estrito para auto-agendamento de bio
        session_conflicts = booking_svc._sessions.find_conflicts(body.scheduled_at)
        booking_conflicts = booking_svc._bookings.find_conflicts(body.scheduled_at)
        if session_conflicts or booking_conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Desculpe, este horário acabou de ser ocupado. Por favor escolha outro.",
            )

        booking_create = BookingCreate(
            patient_name_hint=body.patient_name.strip(),
            patient_phone=body.patient_phone.strip(),
            procedure_id=body.procedure_id,
            scheduled_at=body.scheduled_at,
            note=body.note.strip() if body.note else None,
        )

        booking, _ = booking_svc.create(booking_create)

        return PublicBookingOut(
            id=booking.id,
            professional_name=prof_name,
            professional_slug=prof_slug,
            patient_name=booking.patient_name_hint
            or (booking.patient.name if booking.patient else body.patient_name),
            patient_phone=booking.patient_phone,
            procedure_id=proc.id,
            procedure_name=proc.name,
            procedure_price=proc.price,
            scheduled_at=booking.scheduled_at,
            status=booking.status,
            note=booking.note,
            management_token=booking.management_token,
        )


@router.get("/bookings/{booking_id}", response_model=PublicBookingOut)
def get_public_booking(
    booking_id: UUID,
    token: str = Query(..., min_length=10),
    _rate_limit: PublicQueryRateLimit = None,
) -> PublicBookingOut:
    """Visualiza os detalhes do agendamento usando o link com token privado."""
    _, prof_id = _resolve_booking_tenant(booking_id, token)

    with tenant_session(prof_id) as session:
        booking_svc = _build_booking_service(session, prof_id)
        booking = booking_svc.get_by_token(booking_id, token)

        prof = ProfessionalRepository(session, prof_id).get_by_id(prof_id)

        return PublicBookingOut(
            id=booking.id,
            professional_name=prof.name if prof else "Profissional",
            professional_slug=prof.slug if prof else None,
            patient_name=booking.patient_name_hint
            or (booking.patient.name if booking.patient else "Paciente"),
            patient_phone=booking.patient_phone,
            procedure_id=booking.procedure_id,
            procedure_name=booking.procedure.name if booking.procedure else None,
            procedure_price=booking.procedure.price if booking.procedure else None,
            scheduled_at=booking.scheduled_at,
            status=booking.status,
            note=booking.note,
            management_token=booking.management_token,
        )


@router.patch("/bookings/{booking_id}/reschedule", response_model=PublicBookingOut)
def reschedule_public_booking(
    booking_id: UUID,
    body: PublicBookingReschedule,
    token: str = Query(..., min_length=10),
    _rate_limit: PublicBookingRateLimit = None,
) -> PublicBookingOut:
    """Remarca a data/horário ou procedimento do agendamento pelo próprio paciente."""
    _, prof_id = _resolve_booking_tenant(booking_id, token)

    with tenant_session(prof_id) as session:
        booking_svc = _build_booking_service(session, prof_id)

        if body.procedure_id:
            proc = ProcedureRepository(session, prof_id).get(body.procedure_id)
            if not proc or not proc.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Procedimento selecionado inválido ou inativo.",
                )

        try:
            booking = booking_svc.reschedule_by_token(
                booking_id=booking_id,
                token=token,
                new_time=body.scheduled_at,
                new_procedure_id=body.procedure_id,
                note=body.note,
            )
        except BookingConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except BookingInvalidStateError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        prof = ProfessionalRepository(session, prof_id).get_by_id(prof_id)

        return PublicBookingOut(
            id=booking.id,
            professional_name=prof.name if prof else "Profissional",
            professional_slug=prof.slug if prof else None,
            patient_name=booking.patient_name_hint
            or (booking.patient.name if booking.patient else "Paciente"),
            patient_phone=booking.patient_phone,
            procedure_id=booking.procedure_id,
            procedure_name=booking.procedure.name if booking.procedure else None,
            procedure_price=booking.procedure.price if booking.procedure else None,
            scheduled_at=booking.scheduled_at,
            status=booking.status,
            note=booking.note,
            management_token=booking.management_token,
        )


@router.post("/bookings/{booking_id}/cancel", response_model=PublicBookingOut)
def cancel_public_booking(
    booking_id: UUID,
    token: str = Query(..., min_length=10),
    _rate_limit: PublicBookingRateLimit = None,
) -> PublicBookingOut:
    """Cancela o agendamento pelo próprio paciente via link com token privado."""
    _, prof_id = _resolve_booking_tenant(booking_id, token)

    with tenant_session(prof_id) as session:
        booking_svc = _build_booking_service(session, prof_id)

        try:
            booking = booking_svc.cancel_by_token(booking_id, token)
        except BookingInvalidStateError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        prof = ProfessionalRepository(session, prof_id).get_by_id(prof_id)

        return PublicBookingOut(
            id=booking.id,
            professional_name=prof.name if prof else "Profissional",
            professional_slug=prof.slug if prof else None,
            patient_name=booking.patient_name_hint
            or (booking.patient.name if booking.patient else "Paciente"),
            patient_phone=booking.patient_phone,
            procedure_id=booking.procedure_id,
            procedure_name=booking.procedure.name if booking.procedure else None,
            procedure_price=booking.procedure.price if booking.procedure else None,
            scheduled_at=booking.scheduled_at,
            status=booking.status,
            note=booking.note,
            management_token=booking.management_token,
        )
