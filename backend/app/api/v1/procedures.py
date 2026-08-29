from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ProcedureSvc
from app.schemas.procedure import ProcedureCreate, ProcedureOut, ProcedureUpdate
from app.services.procedure_service import ProcedureNotFoundError

router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.post("", response_model=ProcedureOut, status_code=status.HTTP_201_CREATED)
def create_procedure(payload: ProcedureCreate, svc: ProcedureSvc) -> ProcedureOut:
    return ProcedureOut.model_validate(svc.create(payload))


@router.get("", response_model=list[ProcedureOut])
def list_procedures(
    svc: ProcedureSvc,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ProcedureOut]:
    return [ProcedureOut.model_validate(p) for p in svc.list(limit=limit, offset=offset)]


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
