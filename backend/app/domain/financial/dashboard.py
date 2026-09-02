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

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.core.money import ZERO, money

MONTHS_PER_YEAR = 12


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
    has_provisional_profit: bool  # T-022b, A-07: alguma sessão PENDING no período
    gross_revenue: Decimal
    net_profit: Decimal
    fixed_expenses_total: Decimal | None  # None fora de period_kind=MONTH
    net_profit_after_fixed_expenses: Decimal | None
    receivable_amount: Decimal  # soma de gross_amount com expected_receipt_date > hoje
    average_margin: Decimal | None  # None se gross_revenue == 0
    sale_count: int
    session_count: int
    average_ticket: Decimal | None  # None se sale_count == 0


def _monthly_equivalent(expense: FixedExpenseForDashboard) -> Decimal:
    if expense.periodicity == "YEARLY":
        return money(expense.amount / MONTHS_PER_YEAR)
    return money(expense.amount)


def build_dashboard(
    *,
    sales: list[SaleForDashboard],
    session_count: int,
    fixed_expenses: list[FixedExpenseForDashboard],
    period_kind: PeriodKind,
    today: date,
    has_any_sale_ever: bool,
    has_pending_session_in_period: bool = False,
) -> DashboardResult:
    gross_revenue = money(sum((s.gross_amount for s in sales), ZERO))
    net_profit = money(sum((s.net_profit for s in sales), ZERO))
    receivable = money(
        sum(
            (s.gross_amount for s in sales if s.expected_receipt_date and s.expected_receipt_date > today),
            ZERO,
        )
    )
    sale_count = len(sales)
    average_margin = (net_profit / gross_revenue) if gross_revenue != ZERO else None
    average_ticket = money(gross_revenue / sale_count) if sale_count > 0 else None

    fixed_total = None
    net_after_fixed = None
    if period_kind is PeriodKind.MONTH:
        fixed_total = money(sum((_monthly_equivalent(e) for e in fixed_expenses), ZERO))
        net_after_fixed = money(net_profit - fixed_total)

    return DashboardResult(
        has_any_data=has_any_sale_ever,
        has_provisional_profit=has_pending_session_in_period,
        gross_revenue=gross_revenue,
        net_profit=net_profit,
        fixed_expenses_total=fixed_total,
        net_profit_after_fixed_expenses=net_after_fixed,
        receivable_amount=receivable,
        average_margin=average_margin,
        sale_count=sale_count,
        session_count=session_count,
        average_ticket=average_ticket,
    )
