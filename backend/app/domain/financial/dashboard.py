"""Motor do dashboard financeiro (MVP v6 §13, TASK-022/022a/023).

PURO: sem SQLAlchemy, sem FastAPI, sem I/O (backend/ENGENHARIA.md §5).
Repositories buscam os dados brutos (vendas do período, despesas fixas
vigentes); este módulo só agrega e aplica as regras de negócio:

  - Faturamento/lucro/margem/ticket médio são sobre VENDA (§13.1)
  - Número de sessões é sobre SESSÃO — "3 vendas, 12 atendimentos" não é
    contraditório, é o pacote fazendo o denominador divergir de propósito
  - "Lucro real do mês" = lucro (competência) − despesas fixas vigentes,
    e SÓ aparece em period_kind=MONTH (MVP v7 §12.5) — em "Hoje"/"Últimos
    7 dias" a linha não aparece, não mostra pró-rata
  - Despesa YEARLY entra ratada por 12 no cálculo mensal (v7.1 §12.5)
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.core.money import ZERO, money

MONTHS_PER_YEAR = 12
BREAKEVEN_ALERT_DAYS_BEFORE_MONTH_END = 5


class PeriodKind(StrEnum):
    """Declara o denominador do "Lucro real do mês" (só existe em MONTH).
    Os outros períodos (TODAY, LAST_7_DAYS, CUSTOM) usam as mesmas
    métricas de venda/sessão, só sem a linha de despesas fixas."""

    TODAY = "TODAY"
    LAST_7_DAYS = "LAST_7_DAYS"
    MONTH = "MONTH"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class SaleForDashboard:
    """Recorte de Sale suficiente para agregação — não o model inteiro,
    para o domínio não depender de SQLAlchemy."""

    gross_amount: Decimal
    net_profit: Decimal
    expected_receipt_date: date | None
    sold_at: date


@dataclass(frozen=True)
class FixedExpenseForDashboard:
    amount: Decimal
    periodicity: str  # "MONTHLY" | "YEARLY" — evita import de app.models aqui


@dataclass(frozen=True)
class DashboardResult:
    has_any_data: bool  # T-022a, contrato C-2: first-run vs mês vazio
    gross_revenue: Decimal
    net_profit: Decimal
    fixed_expenses_total: Decimal | None  # None fora de period_kind=MONTH
    net_profit_after_fixed_expenses: Decimal | None
    receivable_amount: Decimal  # soma de gross_amount com expected_receipt_date > hoje
    average_margin: Decimal | None  # None se gross_revenue == 0
    sale_count: int
    session_count: int
    average_ticket: Decimal | None  # None se sale_count == 0
    # Anti-No-Show (EPIC-S2-02, TASK-BACK-S2-11)
    no_show_count: int | None = None
    no_show_rate: Decimal | None = None
    # Épico C — Ponto de equilíbrio do mês (roadmap 2026-09-02). None
    # fora de period_kind=MONTH, igual fixed_expenses_total.
    breakeven_remaining_amount: Decimal | None = None
    # Estimativa (I7): None sem histórico de ticket médio recente para
    # basear a conta — não força um número sem fundamento.
    breakeven_remaining_sessions_estimate: int | None = None
    # True só no mês CORRENTE em andamento, a poucos dias do
    # fechamento, sem ter batido o breakeven ainda.
    breakeven_alert: bool = False


def calculate_recent_average_ticket(sales: list[SaleForDashboard]) -> Decimal | None:
    """Ticket médio de um conjunto de vendas já filtrado pelo caller
    (tipicamente os últimos meses FECHADOS, não o mês corrente — que
    fica enviesado nos primeiros dias). Base do §12.5-C, roadmap
    2026-09-02: estimativa de atendimentos para bater o breakeven."""
    if not sales:
        return None
    gross_revenue = money(sum((s.gross_amount for s in sales), ZERO))
    return money(gross_revenue / len(sales))


def _monthly_equivalent(expense: FixedExpenseForDashboard) -> Decimal:
    if expense.periodicity == "YEARLY":
        return money(expense.amount / MONTHS_PER_YEAR)
    return money(expense.amount)


def build_dashboard(
    *,
    sales: list[SaleForDashboard],
    session_count: int,
    no_show_count: int = 0,
    fixed_expenses: list[FixedExpenseForDashboard],
    period_kind: PeriodKind,
    today: date,
    date_to: date,
    has_any_sale_ever: bool,
    average_ticket_recent: Decimal | None = None,
) -> DashboardResult:
    gross_revenue = money(sum((s.gross_amount for s in sales), ZERO))
    net_profit = money(sum((s.net_profit for s in sales), ZERO))
    receivable = money(
        sum(
            (
                s.gross_amount
                for s in sales
                if s.expected_receipt_date and s.expected_receipt_date > today
            ),
            ZERO,
        )
    )
    sale_count = len(sales)
    average_margin = (net_profit / gross_revenue) if gross_revenue != ZERO else None
    average_ticket = money(gross_revenue / sale_count) if sale_count > 0 else None

    # Cálculo da taxa de No-Show: no_show / (completed + no_show)
    total_appointments = session_count + no_show_count
    no_show_rate = None
    if total_appointments > 0:
        no_show_rate = (Decimal(no_show_count) / Decimal(total_appointments)).quantize(
            Decimal("0.0001")
        )

    fixed_total = None
    net_after_fixed = None
    breakeven_remaining = None
    breakeven_sessions_estimate = None
    breakeven_alert = False
    if period_kind is PeriodKind.MONTH:
        fixed_total = money(sum((_monthly_equivalent(e) for e in fixed_expenses), ZERO))
        net_after_fixed = money(net_profit - fixed_total)
        breakeven_remaining = money(max(ZERO, fixed_total - net_profit))

        if breakeven_remaining == ZERO:
            # Já bateu a meta: são zero atendimentos que faltam,
            # independente de haver histórico de ticket médio ou não —
            # não é uma estimativa, é a conta exata (I7).
            breakeven_sessions_estimate = 0
        elif average_ticket_recent is not None and average_ticket_recent > ZERO:
            breakeven_sessions_estimate = int(
                (breakeven_remaining / average_ticket_recent).to_integral_value(
                    rounding="ROUND_CEILING"
                )
            )

        is_current_month_in_progress = date_to == today
        if is_current_month_in_progress and breakeven_remaining > ZERO:
            last_day_of_month = monthrange(today.year, today.month)[1]
            days_left = last_day_of_month - today.day
            breakeven_alert = days_left <= BREAKEVEN_ALERT_DAYS_BEFORE_MONTH_END

    return DashboardResult(
        has_any_data=has_any_sale_ever,
        gross_revenue=gross_revenue,
        net_profit=net_profit,
        fixed_expenses_total=fixed_total,
        net_profit_after_fixed_expenses=net_after_fixed,
        receivable_amount=receivable,
        average_margin=average_margin,
        sale_count=sale_count,
        session_count=session_count,
        average_ticket=average_ticket,
        no_show_count=no_show_count,
        no_show_rate=no_show_rate,
        breakeven_remaining_amount=breakeven_remaining,
        breakeven_remaining_sessions_estimate=breakeven_sessions_estimate,
        breakeven_alert=breakeven_alert,
    )
