from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import RetentionSvc
from app.domain.retention.state_machine import InvalidReturnOpportunityTransitionError
from app.schemas.retention import (
    PatientRetentionCardOut,
    ReengagementResponseOut,
    ReturnOpportunityOut,
    ReturnOpportunityUpdate,
)
from app.services.retention_service import ReturnOpportunityNotFoundError

router = APIRouter(prefix="/retention", tags=["retention"])


@router.get(
    "/opportunities",
    response_model=list[PatientRetentionCardOut] | list[ReturnOpportunityOut],
)
def get_retention_opportunities(
    svc: RetentionSvc,
    view: str = Query(
        default="cards",
        description="'cards' para visualização agrupada por paciente, 'all' para lista crua",
    ),
    reference_date: date | None = Query(default=None),
) -> list[PatientRetentionCardOut] | list[ReturnOpportunityOut]:
    """Retorna as oportunidades do motor de retorno (TASK-029, TASK-030)."""
    if view == "all":
        return svc.list_all()
    return svc.list_cards(reference_date=reference_date)


@router.get("/reengagement", response_model=ReengagementResponseOut)
def get_retention_reengagement(
    svc: RetentionSvc,
    inactive_days: int = Query(
        default=60,
        ge=1,
        description="Considera 'parado' quem não trata há mais de N dias (F4-03, variável por chamada)",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> ReengagementResponseOut:
    """F4-04: pacientes nunca tratados ou inativos há N dias — reengajamento,
    fonte separada do motor de retorno real (I6/I7). Página compartilhada
    pelas duas seções (never_treated/inactive)."""
    return svc.list_reengagement(inactive_days, page=page, page_size=page_size)


@router.patch("/opportunities/{opp_id}", response_model=ReturnOpportunityOut)
@router.patch("/{opp_id}", response_model=ReturnOpportunityOut)
def update_retention_opportunity(
    opp_id: UUID,
    payload: ReturnOpportunityUpdate,
    svc: RetentionSvc,
) -> ReturnOpportunityOut:
    """Registra contato ou altera status de uma oportunidade de retorno (TASK-031)."""
    try:
        opp = svc.update(opp_id, payload)
        # Converte para output
        items = svc.list_all()
        for it in items:
            if it.id == opp.id:
                return it
        return ReturnOpportunityOut.model_validate(opp)
    except ReturnOpportunityNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Oportunidade de retorno não encontrada"
        ) from exc
    except InvalidReturnOpportunityTransitionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
