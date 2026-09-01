from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ProcedureSvc
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureFromTemplateCreate,
    ProcedureOut,
    ProcedureTemplateOut,
    ProcedureUpdate,
)
from app.services.procedure_service import (
    ProcedureAlreadyExistsError,
    ProcedureNotFoundError,
)

router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.post("", response_model=ProcedureOut, status_code=status.HTTP_201_CREATED)
def create_procedure(payload: ProcedureCreate, svc: ProcedureSvc) -> ProcedureOut:
    return ProcedureOut.model_validate(svc.create(payload))


@router.get("/templates", response_model=list[ProcedureTemplateOut])
def list_procedure_templates(svc: ProcedureSvc) -> list[ProcedureTemplateOut]:
    """Retorna templates de procedimentos do mercado de estética (EPIC-S2-04, TASK-BACK-S2-17)."""
    return svc.list_templates()


@router.post("/from-template", response_model=ProcedureOut, status_code=status.HTTP_201_CREATED)
def create_procedure_from_template(
    payload: ProcedureFromTemplateCreate, svc: ProcedureSvc
) -> ProcedureOut:
    """Cria procedimento a partir de um template pré-definido (EPIC-S2-04, TASK-BACK-S2-19)."""
    try:
        procedure = svc.create_from_template(payload)
        return ProcedureOut.model_validate(procedure)
    except ProcedureAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("", response_model=list[ProcedureOut])
def list_procedures(
    svc: ProcedureSvc,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ProcedureOut]:
    return [
        ProcedureOut.model_validate(p) for p in svc.list(limit=limit, offset=offset)
    ]


@router.get("/{procedure_id}", response_model=ProcedureOut)
def get_procedure(procedure_id: UUID, svc: ProcedureSvc) -> ProcedureOut:
    try:
        procedure = svc.get(procedure_id)
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Procedimento não encontrado"
        ) from exc
    return ProcedureOut.model_validate(procedure)


@router.patch("/{procedure_id}", response_model=ProcedureOut)
def update_procedure(
    procedure_id: UUID, payload: ProcedureUpdate, svc: ProcedureSvc
) -> ProcedureOut:
    try:
        procedure = svc.update(procedure_id, payload)
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Procedimento não encontrado"
        ) from exc
    return ProcedureOut.model_validate(procedure)


@router.delete("/{procedure_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_procedure(procedure_id: UUID, svc: ProcedureSvc) -> None:
    try:
        svc.deactivate(procedure_id)
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Procedimento não encontrado"
        ) from exc
