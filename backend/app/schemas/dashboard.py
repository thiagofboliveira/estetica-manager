from datetime import date

from app.schemas.base import OutputSchema
from app.schemas.types import MoneyOut, RateOut


class DashboardOut(OutputSchema):
    period: str
    date_from: date
    date_to: date

    has_any_data: bool
    has_provisional_profit: bool

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
