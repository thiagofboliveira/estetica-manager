"""DashboardService — orquestra GET /dashboard (MVP v6 §13 TASK-022,
TASK-022a, TASK-023).

Camada de orquestração (backend/ENGENHARIA.md §5): busca dados brutos
via repository, converte para os dataclasses puros de domain/financial/,
chama build_dashboard(). O CÁLCULO em si vive em domain/ — testável sem
banco (tests/test_dashboard.py).
"""

from datetime import date

from app.core.tz import today_in_timezone
from app.domain.financial.dashboard import (
    DashboardResult,
    FixedExpenseForDashboard,
    SaleForDashboard,
    build_dashboard,
)
from app.domain.financial.period import ResolvedPeriod, resolve_period
from app.repositories.fixed_expense import FixedExpenseRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.sale import SaleRepository
from app.repositories.session import SessionRepository


class DashboardService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        session_repo: SessionRepository,
        fixed_expense_repo: FixedExpenseRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._sales = sale_repo
        self._sessions = session_repo
        self._fixed_expenses = fixed_expense_repo
        self._professionals = professional_repo

    def get_dashboard(
        self,
        *,
        filter_name: str,
        custom_from: date | None = None,
        custom_to: date | None = None,
    ) -> tuple[DashboardResult, ResolvedPeriod]:
        professional = self._professionals.get_current()
        today = today_in_timezone(professional.timezone)

        period = resolve_period(
            filter_name=filter_name,
            today=today,
            custom_from=custom_from,
            custom_to=custom_to,
        )

        sales = [
            SaleForDashboard(
                gross_amount=s.gross_amount,
                net_profit=s.net_profit,
                expected_receipt_date=s.expected_receipt_date,
                sold_at=s.sold_at,
            )
            for s in self._sales.list_in_period(period.date_from, period.date_to)
        ]
        session_count = self._sessions.count_completed_in_period(
            period.date_from, period.date_to, professional.timezone
        )
        no_show_count = self._sessions.count_no_show_in_period(
            period.date_from, period.date_to, professional.timezone
        )
        fixed_expenses = [
            FixedExpenseForDashboard(amount=e.amount, periodicity=e.periodicity.value)
            for e in self._fixed_expenses.list_active()
        ]

        result = build_dashboard(
            sales=sales,
            session_count=session_count,
            no_show_count=no_show_count,
            fixed_expenses=fixed_expenses,
            period_kind=period.kind,
            today=today,
            has_any_sale_ever=self._sales.has_any_sale(),
        )
        return result, period

    def get_receivables_projection(
        self, *, months_ahead: int = 12
    ):
        from app.domain.financial.receivables import (
            SaleReceivableInput,
            project_monthly_receivables,
        )

        professional = self._professionals.get_current()
        today = today_in_timezone(professional.timezone)

        sales_models = self._sales.list(limit=5000)
        sales_inputs = [
            SaleReceivableInput(
                sale_id=str(s.id),
                sold_at=s.sold_at,
                payment_method=s.payment_method.value
                if hasattr(s.payment_method, "value")
                else str(s.payment_method),
                installments=s.installments,
                net_received_amount=s.gross_amount - s.fee_amount_applied,
                is_anticipated=False,
            )
            for s in sales_models
            if s.status.value == "ACTIVE"
        ]

        return project_monthly_receivables(
            sales=sales_inputs,
            reference_date=today,
            months_ahead=months_ahead,
        )

