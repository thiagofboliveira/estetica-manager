"""AI-05: medição do uso dos rascunhos de IA."""

from typing import Literal

from fastapi import APIRouter

from app.api.deps import AITextSvc, CurrentProfessional, RetentionSvc
from app.schemas.base import InputSchema, OutputSchema

router = APIRouter(prefix="/ai", tags=["ai"])


class DraftFeedbackIn(InputSchema):
    outcome: Literal["sent", "sent_edited"]


class AIUsageOut(OutputSchema):
    limit: int
    generated: int
    remaining: int
    fallbacks: int
    sent: int
    sent_edited: int


@router.post("/drafts/feedback", status_code=204)
def draft_feedback(
    payload: DraftFeedbackIn,
    ai: AITextSvc,
    retention: RetentionSvc,
    _pid: CurrentProfessional,
) -> None:
    """A profissional enviou um rascunho da IA (com ou sem edição). Só conta;
    não guarda o texto."""
    ai.record_feedback(
        period_month=retention.today().replace(day=1),
        edited=payload.outcome == "sent_edited",
    )


@router.get("/usage", response_model=AIUsageOut)
def get_usage(ai: AITextSvc, retention: RetentionSvc) -> AIUsageOut:
    """Uso do mês: gerados, enviados, editados, texto padrão e quanto resta."""
    return AIUsageOut(**ai.usage(retention.today().replace(day=1)))
