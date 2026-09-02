from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ProfessionalTimezone, RetentionSvc
from app.core.tz import today_in_timezone
from app.domain.retention.return_opportunity_state_machine import (
    InvalidReturnOpportunityTransitionError,
)
from app.schemas.retention import (
    PatientRetentionOut,
    ReturnOpportunityOut,
    ReturnOpportunityUpdate,
)
from app.services.retention_service import ReturnOpportunityNotFoundError

router = APIRouter(prefix="/retention", tags=["retention"])


@router.get("/opportunities", response_model=list[PatientRetentionOut])
def list_opportunities(
    svc: RetentionSvc, timezone: ProfessionalTimezone
) -> list[PatientRetentionOut]:
    groups = svc.list_for_reactivation_screen(
        today=today_in_timezone(timezone), professional_timezone=timezone
    )
    return [PatientRetentionOut.model_validate(g) for g in groups]


@router.patch("/opportunities/{opportunity_id}", response_model=ReturnOpportunityOut)
def update_opportunity(
    opportunity_id: UUID,
    payload: ReturnOpportunityUpdate,
    svc: RetentionSvc,
    timezone: ProfessionalTimezone,
) -> ReturnOpportunityOut:
    try:
        opportunity = svc.update_status(
            opportunity_id,
            payload.status,
            payload.contact_channel,
            professional_timezone=timezone,
        )
    except ReturnOpportunityNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Oportunidade não encontrada"
        ) from exc
    except InvalidReturnOpportunityTransitionError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"transição inválida: {exc.current} -> {exc.target}",
        ) from exc
    return ReturnOpportunityOut.model_validate(opportunity)
