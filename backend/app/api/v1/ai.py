"""AI-05: medição do uso dos rascunhos de IA."""

from typing import Literal

from fastapi import APIRouter
from pydantic import Field

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


class MapColumnsIn(InputSchema):
    headers: list[str] = Field(min_length=1, max_length=50)
    sample_rows: list[list[str]] = Field(default_factory=list, max_length=5)


class MapColumnsOut(OutputSchema):
    name: int | None
    phone: int | None
    email: int | None
    notes: int | None
    last_visit_date: int | None
    source: Literal["ai", "fallback"]


@router.post("/import/map-columns", response_model=MapColumnsOut)
def map_columns(
    payload: MapColumnsIn,
    ai: AITextSvc,
    retention: RetentionSvc,
    _pid: CurrentProfessional,
) -> MapColumnsOut:
    """AI-08: sugere qual coluna da planilha é nome/telefone/e-mail/etc. Só
    cabeçalhos e exemplos mascarados chegam à IA; a importação em si segue pelo
    ``POST /patients/import`` de sempre."""
    mapping, source = ai.map_columns(
        headers=payload.headers,
        sample_rows=payload.sample_rows,
        period_month=retention.today().replace(day=1),
    )
    return MapColumnsOut(**mapping, source=source)
