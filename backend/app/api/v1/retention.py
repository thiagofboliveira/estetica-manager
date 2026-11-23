from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AITextSvc, EventSvc, RetentionSvc
from app.domain.ai.reengagement_message import Kind
from app.domain.events import EventName
from app.domain.retention.enums import ReturnOpportunityStatus
from app.domain.retention.state_machine import InvalidReturnOpportunityTransitionError
from app.schemas.retention import (
    DraftMessageOut,
    PatientRetentionCardOut,
    ReengagementResponseOut,
    ReturnOpportunityOut,
    ReturnOpportunityUpdate,
)
from app.services.retention_service import (
    DraftNotAllowedError,
    ReturnOpportunityNotFoundError,
)

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
    events: EventSvc,
) -> ReturnOpportunityOut:
    """Registra contato ou altera status de uma oportunidade de retorno (TASK-031)."""
    try:
        opp = svc.update(opp_id, payload)

        if (
            payload.status == ReturnOpportunityStatus.CONTACTED
            or payload.contact_channel is not None
            or payload.contacted_at is not None
            or opp.contacted_at is not None
        ):
            events.track_first(EventName.FIRST_REACTIVATION_SENT)

        if payload.status in (
            ReturnOpportunityStatus.BOOKED,
            ReturnOpportunityStatus.CLOSED,
        ):
            events.track_first(EventName.FIRST_REACTIVATION_CONVERTED)

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


@router.post(
    "/opportunities/{opp_id}/draft-message", response_model=DraftMessageOut
)
def draft_return_message(
    opp_id: UUID, svc: RetentionSvc, ai: AITextSvc
) -> DraftMessageOut:
    """AI-02: rascunho de WhatsApp para chamar a paciente de volta.

    Só texto: nada é enviado e a oportunidade não muda de status. Exige
    consentimento de WhatsApp e respeita quem pediu para não receber. Sem IA
    disponível (sem chave, teto do mês, erro), devolve o texto fixo."""
    try:
        ctx, today = svc.draft_context(opp_id)
    except ReturnOpportunityNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Oportunidade de retorno não encontrada"
        ) from exc
    except DraftNotAllowedError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Esta paciente não autorizou contato por WhatsApp",
        ) from exc
    result = ai.draft_return_message(ctx, period_month=today.replace(day=1))
    return DraftMessageOut(
        text=result.text,
        source=result.source,
        fallback_reason=result.reason,
        remaining_drafts=result.remaining,
    )


@router.post(
    "/reengagement/{patient_id}/draft-message", response_model=DraftMessageOut
)
def draft_reengagement_message(
    patient_id: UUID,
    kind: Annotated[Kind, Query(description="never_treated ou inactive")],
    svc: RetentionSvc,
    ai: AITextSvc,
) -> DraftMessageOut:
    """AI-06: rascunho de WhatsApp para uma paciente que parou de voltar ou
    nunca tratou. Só texto, sem procedimento, valor nem dado clínico; exige
    consentimento de WhatsApp. Sem IA disponível, devolve o texto fixo."""
    try:
        ctx, today = svc.reengagement_context(patient_id, kind)
    except ReturnOpportunityNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc
    except DraftNotAllowedError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Esta paciente não autorizou contato por WhatsApp",
        ) from exc
    result = ai.draft_reengagement_message(ctx, period_month=today.replace(day=1))
    return DraftMessageOut(
        text=result.text,
        source=result.source,
        fallback_reason=result.reason,
        remaining_drafts=result.remaining,
    )
