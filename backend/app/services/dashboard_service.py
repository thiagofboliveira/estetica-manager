"""DashboardService — orquestra GET /dashboard (MVP v6 §13 TASK-022,
TASK-022a, TASK-023).

Camada de orquestração (backend/ENGENHARIA.md §5): busca dados brutos
via repository, converte para os dataclasses puros de domain/financial/,
chama build_dashboard(). O CÁLCULO em si vive em domain/ — testável sem
banco (tests/test_dashboard.py).
"""

from datetime import date
from uuid import UUID

from app.core.tz import today_in_timezone
from app.domain.financial.dashboard import (
    DashboardResult,
    FixedExpenseForDashboard,
    PeriodKind,
    SaleForDashboard,
    build_dashboard,
    calculate_recent_average_ticket,
)
from app.domain.financial.period import (
    ResolvedPeriod,
    last_n_closed_months_range,
    resolve_period,
)
from app.repositories.fixed_expense import FixedExpenseRepository
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.sale import SaleRepository
from app.repositories.session import SessionRepository

RECENT_TICKET_MONTHS = 3


class DashboardService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        session_repo: SessionRepository,
        fixed_expense_repo: FixedExpenseRepository,
        professional_repo: ProfessionalRepository,
        financial_settings_repo: FinancialSettingsRepository | None = None,
    ) -> None:
        self._sales = sale_repo
        self._sessions = session_repo
        self._fixed_expenses = fixed_expense_repo
        self._professionals = professional_repo
        self._financial_settings = financial_settings_repo

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

        # Ticket médio recente só é relevante no mês CORRENTE em
        # andamento (onde o breakeven se aplica) — evita uma query
        # extra nos outros filtros (hoje, 7 dias, mês passado, custom).
        average_ticket_recent = None
        if period.kind is PeriodKind.MONTH and period.date_to == today:
            recent_from, recent_to = last_n_closed_months_range(
                today, n=RECENT_TICKET_MONTHS
            )
            recent_sales = self._sales.list_in_period(recent_from, recent_to)
            average_ticket_recent = calculate_recent_average_ticket(
                [
                    SaleForDashboard(
                        gross_amount=s.gross_amount,
                        net_profit=s.net_profit,
                        expected_receipt_date=s.expected_receipt_date,
                        sold_at=s.sold_at,
                    )
                    for s in recent_sales
                ]
            )

        monthly_revenue_goal = None
        if self._financial_settings is not None:
            settings_obj = self._financial_settings.get_singleton()
            if settings_obj and settings_obj.monthly_revenue_goal is not None:
                monthly_revenue_goal = settings_obj.monthly_revenue_goal

        result = build_dashboard(
            sales=sales,
            session_count=session_count,
            no_show_count=no_show_count,
            fixed_expenses=fixed_expenses,
            period_kind=period.kind,
            today=today,
            date_to=period.date_to,
            has_any_sale_ever=self._sales.has_any_sale(),
            average_ticket_recent=average_ticket_recent,
            monthly_revenue_goal=monthly_revenue_goal,
        )
        return result, period

    def get_receivables_projection(self, *, months_ahead: int = 12):
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
                is_anticipated=bool(
                    (s.snapshot_payload or {}).get("anticipates_all", False)
                ),
            )
            for s in sales_models
            if s.status.value == "ACTIVE"
        ]

        return project_monthly_receivables(
            sales=sales_inputs,
            reference_date=today,
            months_ahead=months_ahead,
        )

    def get_aggregated_dashboard(
        self,
        *,
        professional_ids: list[UUID],
        filter_name: str,
        custom_from: date | None = None,
        custom_to: date | None = None,
    ) -> tuple[DashboardResult, ResolvedPeriod]:
        from app.db.session import tenant_session

        professional = self._professionals.get_current()
        today = today_in_timezone(professional.timezone)

        period = resolve_period(
            filter_name=filter_name,
            today=today,
            custom_from=custom_from,
            custom_to=custom_to,
        )

        all_sales: list[SaleForDashboard] = []
        total_session_count = 0
        total_no_show_count = 0
        all_fixed_expenses: list[FixedExpenseForDashboard] = []
        has_any_sale = False
        all_recent_sales: list[SaleForDashboard] = []

        is_current_month = period.kind is PeriodKind.MONTH and period.date_to == today
        recent_from, recent_to = (
            last_n_closed_months_range(today, n=RECENT_TICKET_MONTHS)
            if is_current_month
            else (None, None)
        )

        total_monthly_goal = Decimal("0.00")
        has_any_goal = False

        for pid in professional_ids:
            with tenant_session(pid) as sess:
                s_repo = SaleRepository(sess, pid)
                sess_repo = SessionRepository(sess, pid)
                fe_repo = FixedExpenseRepository(sess, pid)
                fs_repo = FinancialSettingsRepository(sess, pid)

                cfg = fs_repo.get_singleton()
                if cfg and cfg.monthly_revenue_goal is not None:
                    total_monthly_goal += cfg.monthly_revenue_goal
                    has_any_goal = True

                if s_repo.has_any_sale():
                    has_any_sale = True

                for s in s_repo.list_in_period(period.date_from, period.date_to):
                    all_sales.append(
                        SaleForDashboard(
                            gross_amount=s.gross_amount,
                            net_profit=s.net_profit,
                            expected_receipt_date=s.expected_receipt_date,
                            sold_at=s.sold_at,
                        )
                    )

                total_session_count += sess_repo.count_completed_in_period(
                    period.date_from, period.date_to, professional.timezone
                )
                total_no_show_count += sess_repo.count_no_show_in_period(
                    period.date_from, period.date_to, professional.timezone
                )

                for e in fe_repo.list_active():
                    all_fixed_expenses.append(
                        FixedExpenseForDashboard(
                            amount=e.amount, periodicity=e.periodicity.value
                        )
                    )

                if is_current_month and recent_from and recent_to:
                    for s in s_repo.list_in_period(recent_from, recent_to):
                        all_recent_sales.append(
                            SaleForDashboard(
                                gross_amount=s.gross_amount,
                                net_profit=s.net_profit,
                                expected_receipt_date=s.expected_receipt_date,
                                sold_at=s.sold_at,
                            )
                        )

        average_ticket_recent = (
            calculate_recent_average_ticket(all_recent_sales)
            if is_current_month
            else None
        )

        result = build_dashboard(
            sales=all_sales,
            session_count=total_session_count,
            no_show_count=total_no_show_count,
            fixed_expenses=all_fixed_expenses,
            period_kind=period.kind,
            today=today,
            date_to=period.date_to,
            has_any_sale_ever=has_any_sale,
            average_ticket_recent=average_ticket_recent,
            monthly_revenue_goal=total_monthly_goal if has_any_goal else None,
        )
        return result, period
