"""Motor do dashboard (MVP v6 §13, TASK-022/022a/023) — puro, sem banco."""

from datetime import date
from decimal import Decimal as D

from app.domain.financial.dashboard import (
    FixedExpenseForDashboard,
    PeriodKind,
    SaleForDashboard,
    build_dashboard,
)
from app.domain.financial.period import resolve_period


def _sale(
    gross: str,
    profit: str,
    receipt: date | None = None,
    sold_at: date = date(2026, 3, 10),
) -> SaleForDashboard:
    return SaleForDashboard(
        gross_amount=D(gross),
        net_profit=D(profit),
        expected_receipt_date=receipt,
        sold_at=sold_at,
    )


class TestHasAnyData:
    """T-022a, contrato C-2: distingue first-run de mês sem venda."""

    def test_sem_venda_nenhuma_e_sem_historico_e_first_run(self) -> None:
        result = build_dashboard(
            sales=[],
            session_count=0,
            fixed_expenses=[],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=False,
        )
        assert result.has_any_data is False

    def test_sem_venda_no_periodo_mas_com_historico_nao_e_first_run(self) -> None:
        result = build_dashboard(
            sales=[],
            session_count=0,
            fixed_expenses=[],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.has_any_data is True
        # Mês vazio: métricas zeradas, não None nem erro.
        assert result.gross_revenue == D("0.00")
        assert result.average_margin is None
        assert result.average_ticket is None


class TestMetricasBasicas:
    def test_faturamento_e_lucro_somam_por_venda(self) -> None:
        sales = [_sale("1000.00", "350.00"), _sale("2000.00", "900.00")]
        result = build_dashboard(
            sales=sales,
            session_count=12,
            fixed_expenses=[],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.gross_revenue == D("3000.00")
        assert result.net_profit == D("1250.00")
        assert result.sale_count == 2
        assert result.session_count == 12  # denominador diferente de propósito (§13.1)

    def test_ticket_medio_e_bruto_sobre_numero_de_vendas(self) -> None:
        sales = [_sale("1000.00", "350.00"), _sale("2000.00", "900.00")]
        result = build_dashboard(
            sales=sales,
            session_count=0,
            fixed_expenses=[],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.average_ticket == D("1500.00")

    def test_margem_media_e_lucro_sobre_faturamento(self) -> None:
        sales = [_sale("1000.00", "350.00")]
        result = build_dashboard(
            sales=sales,
            session_count=0,
            fixed_expenses=[],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.average_margin == D("0.35")

    def test_receber_soma_so_vendas_com_recebimento_futuro(self) -> None:
        sales = [
            _sale("1000.00", "350.00", receipt=date(2026, 4, 20)),  # futuro
            _sale("500.00", "200.00", receipt=date(2026, 3, 1)),  # já passou
            _sale("300.00", "100.00", receipt=None),  # sem data
        ]
        result = build_dashboard(
            sales=sales,
            session_count=0,
            fixed_expenses=[],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.receivable_amount == D("1000.00")


class TestLucroRealDoMes:
    """MVP v7 §12.5: só aparece em period_kind=MONTH."""

    def test_so_aparece_em_month(self) -> None:
        expenses = [FixedExpenseForDashboard(amount=D("800.00"), periodicity="MONTHLY")]
        for kind in (PeriodKind.TODAY, PeriodKind.LAST_7_DAYS, PeriodKind.CUSTOM):
            result = build_dashboard(
                sales=[_sale("1000.00", "350.00")],
                session_count=0,
                fixed_expenses=expenses,
                period_kind=kind,
                today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
                has_any_sale_ever=True,
            )
            assert result.fixed_expenses_total is None, kind
            assert result.net_profit_after_fixed_expenses is None, kind

    def test_desconta_despesa_mensal_direto(self) -> None:
        expenses = [FixedExpenseForDashboard(amount=D("800.00"), periodicity="MONTHLY")]
        result = build_dashboard(
            sales=[_sale("1000.00", "350.00")],
            session_count=0,
            fixed_expenses=expenses,
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.fixed_expenses_total == D("800.00")
        assert result.net_profit_after_fixed_expenses == D("-450.00")

    def test_despesa_anual_e_rateada_por_12(self) -> None:
        # Taxa de vigilância sanitária: R$1200/ano -> R$100/mês.
        expenses = [FixedExpenseForDashboard(amount=D("1200.00"), periodicity="YEARLY")]
        result = build_dashboard(
            sales=[_sale("1000.00", "350.00")],
            session_count=0,
            fixed_expenses=expenses,
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.fixed_expenses_total == D("100.00")

    def test_mensal_e_anual_somam_juntos(self) -> None:
        expenses = [
            FixedExpenseForDashboard(amount=D("800.00"), periodicity="MONTHLY"),
            FixedExpenseForDashboard(amount=D("1200.00"), periodicity="YEARLY"),
        ]
        result = build_dashboard(
            sales=[],
            session_count=0,
            fixed_expenses=expenses,
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.fixed_expenses_total == D("900.00")


class TestResolvePeriod:
    def test_today(self) -> None:
        p = resolve_period(filter_name="today", today=date(2026, 3, 15))
        assert p.date_from == p.date_to == date(2026, 3, 15)

    def test_last_7_days_e_inclusivo(self) -> None:
        p = resolve_period(filter_name="last_7_days", today=date(2026, 3, 15))
        assert p.date_from == date(2026, 3, 9)
        assert p.date_to == date(2026, 3, 15)
        assert (p.date_to - p.date_from).days == 6

    def test_this_month(self) -> None:
        p = resolve_period(filter_name="this_month", today=date(2026, 3, 15))
        assert p.date_from == date(2026, 3, 1)
        assert p.date_to == date(2026, 3, 15)
        assert p.kind.value == "MONTH"

    def test_last_month_cruzando_ano(self) -> None:
        p = resolve_period(filter_name="last_month", today=date(2026, 1, 15))
        assert p.date_from == date(2025, 12, 1)
        assert p.date_to == date(2025, 12, 31)

    def test_last_month_fevereiro_bissexto(self) -> None:
        p = resolve_period(filter_name="last_month", today=date(2028, 3, 1))
        assert p.date_from == date(2028, 2, 1)
        assert p.date_to == date(2028, 2, 29)  # 2028 é bissexto

    def test_custom_requer_datas(self) -> None:
        p = resolve_period(
            filter_name="custom",
            today=date(2026, 3, 15),
            custom_from=date(2026, 1, 1),
            custom_to=date(2026, 2, 1),
        )
        assert p.date_from == date(2026, 1, 1)
        assert p.date_to == date(2026, 2, 1)

    def test_custom_sem_datas_falha(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            resolve_period(filter_name="custom", today=date(2026, 3, 15))

    def test_custom_from_depois_de_to_falha(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            resolve_period(
                filter_name="custom",
                today=date(2026, 3, 15),
                custom_from=date(2026, 3, 1),
                custom_to=date(2026, 1, 1),
            )
