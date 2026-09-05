from datetime import date

from app.schemas.base import OutputSchema
from app.schemas.types import MoneyOut, RateOut


class DashboardOut(OutputSchema):
    period: str
    date_from: date
    date_to: date

    has_any_data: bool

    gross_revenue: MoneyOut
    net_profit: MoneyOut
    # null fora de filtros mensais (MVP v7 §12.5) — o FRONTEND esconde a
    # linha quando null; a API sempre devolve o campo, nunca omite.
    fixed_expenses_total: MoneyOut | None
    net_profit_after_fixed_expenses: MoneyOut | None
    receivable_amount: MoneyOut

    average_margin: RateOut | None
    sale_count: int
    session_count: int
    average_ticket: MoneyOut | None

    # Anti-No-Show (EPIC-S2-02, TASK-BACK-S2-11)
    no_show_count: int | None = None
    no_show_rate: RateOut | None = None

    # Épico C — Ponto de equilíbrio do mês (roadmap 2026-09-02)
    breakeven_remaining_amount: MoneyOut | None = None
    breakeven_remaining_sessions_estimate: int | None = None
    breakeven_alert: bool = False


class ROIOut(OutputSchema):
    attributed_revenue: MoneyOut
    attributed_sale_count: int
    patients_reactivated: int
    subscription_fee: MoneyOut
    roi_ratio: str | None
    period: str
    date_from: date
    date_to: date
    is_estimated: bool
    # G-11: fonte SEPARADA de attributed_revenue — nunca somada nem
    # incluída em roi_ratio. Sessões que passaram pela confirmação
    # anti-no-show (GET /sessions/unconfirmed) e foram COMPLETED, não
    # NO_SHOW. Rotulado à parte para o frontend não confundir as duas
    # fontes de valor (ver docs/pending/BACKLOG_GO_LIVE.md §6).
    no_show_avoided_count: int
    no_show_avoided_revenue: MoneyOut


class MonthlyReceivableOut(OutputSchema):
    year_month: str
    total_amount: MoneyOut
    installment_count: int


class ReceivablesOut(OutputSchema):
    total_projected_amount: MoneyOut
    months: list[MonthlyReceivableOut]
