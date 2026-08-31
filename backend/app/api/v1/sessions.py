from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import SessionSvc
from app.domain.sales.session_state_machine import InvalidSessionTransitionError
from app.schemas.session import (
    AgendaItemOut,
    OpenPackageOut,
    SessionDetailOut,
    SessionUpdate,
    UnconfirmedSessionOut,
)
from app.services.session_service import SessionNotFoundError

router = APIRouter(prefix="", tags=["sessions"])


@router.get("/sessions", response_model=list[AgendaItemOut])
def get_sessions_agenda(
    svc: SessionSvc,
    date_from: date = Query(alias="from"),
    date_to: date = Query(alias="to"),
) -> list[AgendaItemOut]:
    """Retorna a agenda do período (sessões agendadas + bookings provisórios),
    convertidas no fuso horário da profissional (TASK-032, MVP v6 §16)."""
    if date_to < date_from:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A data final deve ser maior ou igual à data inicial.",
        )
    return svc.get_agenda(date_from, date_to)


@router.get("/sessions/unconfirmed", response_model=list[UnconfirmedSessionOut])
def list_unconfirmed_sessions(svc: SessionSvc) -> list[UnconfirmedSessionOut]:
    """Lista sessões e reservas agendadas para amanhã que ainda não foram confirmadas (EPIC-S2-02, TASK-BACK-S2-06)."""
    return svc.list_unconfirmed()


@router.post("/sessions/{session_id}/confirm", response_model=SessionDetailOut)
def confirm_session(session_id: UUID, svc: SessionSvc) -> SessionDetailOut:
    """Registra a confirmação de presença da sessão (EPIC-S2-02, TASK-BACK-S2-10)."""
    try:
        session = svc.confirm(session_id)
        return SessionDetailOut.model_validate(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sessão não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/packages/open", response_model=list[OpenPackageOut])
def get_open_packages(svc: SessionSvc) -> list[OpenPackageOut]:
    """Lista pacotes com saldo de sessões em aberto / não agendadas (TASK-034)."""
    return svc.get_open_packages()


@router.patch("/sessions/{session_id}", response_model=SessionDetailOut)
def update_session(
    session_id: UUID,
    payload: SessionUpdate,
    svc: SessionSvc,
    response: Response,
) -> SessionDetailOut:
    """Atualiza sessão: data/hora, status, observações ou custo customizado (TASK-016, TASK-033)."""
    try:
        session, warnings = svc.update(session_id, payload)
        if warnings:
            response.headers["X-Warnings"] = "; ".join(warnings)
        return SessionDetailOut.model_validate(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sessão não encontrada") from exc
    except InvalidSessionTransitionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
