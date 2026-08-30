from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import BookingSvc
from app.domain.bookings.state_machine import InvalidBookingTransitionError
from app.schemas.booking import BookingCreate, BookingOut, BookingUpdate
from app.services.booking_service import BookingNotFoundError

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    svc: BookingSvc,
    response: Response,
) -> BookingOut:
    """Cria um agendamento provisório / reserva de horário (TASK-034b, MVP v7.1 §16.6)."""
    booking, warnings = svc.create(payload)
    if warnings:
        response.headers["X-Warnings"] = "; ".join(warnings)
    return BookingOut.model_validate(booking)


@router.get("", response_model=list[BookingOut])
def list_bookings(
    svc: BookingSvc,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
) -> list[BookingOut]:
    """Lista agendamentos provisórios em intervalo de datas (TASK-034b)."""
    bookings = svc.list_bookings(date_from, date_to)
    return [BookingOut.model_validate(b) for b in bookings]


@router.patch("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: UUID,
    payload: BookingUpdate,
    svc: BookingSvc,
    response: Response,
) -> BookingOut:
    """Atualiza ou cancela um agendamento provisório (TASK-034b)."""
    try:
        booking, warnings = svc.update(booking_id, payload)
        if warnings:
            response.headers["X-Warnings"] = "; ".join(warnings)
        return BookingOut.model_validate(booking)
    except BookingNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Agendamento provisório não encontrado"
        ) from exc
    except InvalidBookingTransitionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
