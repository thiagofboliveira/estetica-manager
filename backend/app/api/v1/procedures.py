from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import EventSvc, ProcedureSvc
from app.domain.catalog.procedure_templates import list_procedure_templates
from app.domain.events import EventName
from app.models.procedure import Procedure, SessionPlan
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureFromTemplateCreate,
    ProcedureListOut,
    ProcedureOut,
    ProcedureSupplyItem,
    ProcedureTemplateOut,
    ProcedureUpdate,
)
from app.services.procedure_service import (
    ProcedureAlreadyExistsError,
    ProcedureNotFoundError,
)

router = APIRouter(prefix="/procedures", tags=["procedures"])


def _to_procedure_out(proc: Procedure) -> ProcedureOut:
    supplies_out: list[ProcedureSupplyItem] = []
    if getattr(proc, "supplies", None):
        for ps in proc.supplies:
            s_name = ps.supply.name if getattr(ps, "supply", None) else None
            u_measure = ps.supply.unit_measure if getattr(ps, "supply", None) else None
            cost = ps.supply.cost_price if getattr(ps, "supply", None) else None
            subtotal = (cost * ps.quantity) if cost is not None else None
            supplies_out.append(
                ProcedureSupplyItem(
                    supply_id=ps.supply_id,
                    quantity=ps.quantity,
                    supply_name=s_name,
                    unit_measure=u_measure,
                    cost_price=str(cost) if cost is not None else None,
                    subtotal_cost=str(subtotal) if subtotal is not None else None,
                )
            )

    out = ProcedureOut.model_validate(proc)
    out.supplies = supplies_out
    return out


@router.post("", response_model=ProcedureOut, status_code=status.HTTP_201_CREATED)
def create_procedure(
    payload: ProcedureCreate, svc: ProcedureSvc, events: EventSvc
) -> ProcedureOut:
    procedure = svc.create(payload)
    # G-13: emitido na rota, não no service — evita alterar a assinatura
    # de ProcedureService (e seus testes) só para injetar telemetria.
    events.track_first(EventName.FIRST_PROCEDURE_CREATED)
    return _to_procedure_out(procedure)


@router.get("/templates", response_model=list[ProcedureTemplateOut])
def get_procedure_templates() -> list[ProcedureTemplateOut]:
    """Templates públicos de procedimentos do mercado de estética, sem
    autenticação, para uso na landing page e no onboarding pré-login
    (EPIC-S2-04, TASK-BACK-S2-17)."""
    templates = list_procedure_templates()
    return [
        ProcedureTemplateOut(
            template_id=t.template_id,
            name=t.name,
            type=t.type,
            suggested_price=t.suggested_price,
            suggested_cost=t.suggested_cost,
            suggested_return_interval_days=t.suggested_return_interval_days,
            category=t.category,
            is_suggested=t.is_suggested,
        )
        for t in templates
    ]


@router.post(
    "/from-template", response_model=ProcedureOut, status_code=status.HTTP_201_CREATED
)
def create_procedure_from_template(
    payload: ProcedureFromTemplateCreate, svc: ProcedureSvc
) -> ProcedureOut:
    """Cria procedimento a partir de um template pré-definido (EPIC-S2-04, TASK-BACK-S2-19)."""
    try:
        procedure = svc.create_from_template(payload)
        return _to_procedure_out(procedure)
    except ProcedureAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("", response_model=ProcedureListOut)
def list_procedures(
    svc: ProcedureSvc,
    is_invasive: bool | None = Query(default=None),
    session_plan: SessionPlan | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> ProcedureListOut:
    offset = (page - 1) * page_size
    items = svc.list(
        limit=page_size,
        offset=offset,
        is_invasive=is_invasive,
        session_plan=session_plan,
    )
    return ProcedureListOut(
        items=[_to_procedure_out(p) for p in items],
        total_count=svc.count(is_invasive=is_invasive, session_plan=session_plan),
        page=page,
        page_size=page_size,
    )


@router.get("/{procedure_id}", response_model=ProcedureOut)
def get_procedure(procedure_id: UUID, svc: ProcedureSvc) -> ProcedureOut:
    try:
        procedure = svc.get(procedure_id)
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Procedimento não encontrado"
        ) from exc
    return _to_procedure_out(procedure)


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
    return _to_procedure_out(procedure)


@router.delete("/{procedure_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_procedure(procedure_id: UUID, svc: ProcedureSvc) -> None:
    try:
        svc.deactivate(procedure_id)
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Procedimento não encontrado"
        ) from exc
