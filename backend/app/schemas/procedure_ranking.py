from datetime import date
from uuid import UUID

from app.schemas.base import OutputSchema
from app.schemas.types import MoneyOut, RateOut


class ProcedureRankingRowOut(OutputSchema):
    procedure_id: UUID
    procedure_name: str
    gross_revenue: MoneyOut
    net_profit: MoneyOut
    margin: RateOut | None
    session_count: int


class ProcedureRankingOut(OutputSchema):
    period: str
    date_from: date
    date_to: date
    rows: list[ProcedureRankingRowOut]
    total_count: int
    page: int
    page_size: int
    scope: str = "me"
    professionals_count: int = 1


class LossAlertOut(OutputSchema):
    """AI-04: procedimento com prejuízo ou margem baixa. Calculado pelo backend."""

    procedure_id: UUID
    procedure_name: str
    kind: str  # "loss" | "low_margin"
    gross_revenue: MoneyOut
    net_profit: MoneyOut
    margin_percent: int | None
    session_count: int


class LossAlertsOut(OutputSchema):
    period: str
    date_from: date
    date_to: date
    alerts: list[LossAlertOut]


class LossAlertExplanationOut(OutputSchema):
    text: str
    source: str  # "ai" | "fallback"
    fallback_reason: str | None
    remaining_drafts: int
