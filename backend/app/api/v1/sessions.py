from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionSvc
from app.domain.sales.session_state_machine import InvalidSessionTransitionError
from app.schemas.session import SessionDetailOut, SessionUpdate
from app.services.session_service import SessionNotFoundError

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.patch("/{session_id}", response_model=SessionDetailOut)
def update_session(
    session_id: UUID, payload: SessionUpdate, svc: SessionSvc
) -> SessionDetailOut:
    try:
        session = svc.update_status(session_id, payload.status)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Sessão não encontrada"
        ) from exc
    except InvalidSessionTransitionError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"transição inválida: {exc.current} -> {exc.target}",
        ) from exc
    return SessionDetailOut.model_validate(session)
