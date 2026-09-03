"""Resolução de período do dashboard (MVP v6 §13, TASK-023).

PURO — sem I/O. Recebe "hoje" já calculado no fuso da profissional
(app.core.tz.today_in_timezone) e devolve o intervalo [from, to] em
datas locais, inclusive nos dois extremos.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.financial.dashboard import PeriodKind

LAST_7_DAYS_SPAN = 6  # hoje + 6 dias atrás = 7 dias inclusive


@dataclass(frozen=True)
class ResolvedPeriod:
    kind: PeriodKind
    date_from: date
    date_to: date


def resolve_period(
    *,
    filter_name: str,
    today: date,
    custom_from: date | None = None,
    custom_to: date | None = None,
) -> ResolvedPeriod:
    """filter_name: "today" | "last_7_days" | "this_month" | "last_month" | "custom"."""
    if filter_name == "today":
        return ResolvedPeriod(PeriodKind.TODAY, today, today)

    if filter_name == "last_7_days":
        return ResolvedPeriod(
            PeriodKind.LAST_7_DAYS, today - timedelta(days=LAST_7_DAYS_SPAN), today
        )

    if filter_name == "this_month":
        start = today.replace(day=1)
        return ResolvedPeriod(PeriodKind.MONTH, start, today)

    if filter_name == "last_month":
        first_of_this_month = today.replace(day=1)
        last_day_prev_month = first_of_this_month - timedelta(days=1)
        start = last_day_prev_month.replace(day=1)
        return ResolvedPeriod(PeriodKind.MONTH, start, last_day_prev_month)

    if filter_name == "custom":
        if custom_from is None or custom_to is None:
            raise ValueError("custom requer date_from e date_to")
        if custom_from > custom_to:
            raise ValueError("date_from não pode ser depois de date_to")
        return ResolvedPeriod(PeriodKind.CUSTOM, custom_from, custom_to)

    raise ValueError(f"filtro de período desconhecido: {filter_name}")


def last_n_closed_months_range(today: date, n: int) -> tuple[date, date]:
    """[date_from, date_to] cobrindo os N meses FECHADOS anteriores ao
    mês corrente de `today` — usado para a base do ticket médio recente
    (Épico C, roadmap 2026-09-02): nunca inclui o mês em andamento, que
    fica enviesado nos primeiros dias."""
    first_of_this_month = today.replace(day=1)
    date_to = first_of_this_month - timedelta(days=1)

    year, month = date_to.year, date_to.month
    for _ in range(n - 1):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    date_from = date(year, month, 1)

    return date_from, date_to
