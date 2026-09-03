"""Épico C — "Ponto de equilíbrio do mês" (roadmap 2026-09-02). PURO."""

from datetime import date
from decimal import Decimal as D

from app.domain.financial.dashboard import (
    FixedExpenseForDashboard,
    PeriodKind,
    SaleForDashboard,
    build_dashboard,
    calculate_recent_average_ticket,
)


def _sale(gross: str, profit: str, sold_at: date = date(2026, 3, 10)) -> SaleForDashboard:
    return SaleForDashboard(
        gross_amount=D(gross), net_profit=D(profit), expected_receipt_date=None, sold_at=sold_at
    )


def _expense(amount: str) -> FixedExpenseForDashboard:
    return FixedExpenseForDashboard(amount=D(amount), periodicity="MONTHLY")


class TestBreakevenRemainingAmount:
    def test_falta_a_diferenca_entre_despesas_fixas_e_lucro_do_mes(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.breakeven_remaining_amount == D("200.00")

    def test_ja_bateu_o_breakeven_fica_zero_nao_negativo(self) -> None:
        result = build_dashboard(
            sales=[_sale("2000.00", "1200.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.breakeven_remaining_amount == D("0.00")

    def test_fora_do_periodo_mensal_e_none(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.TODAY,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
        )
        assert result.breakeven_remaining_amount is None


class TestBreakevenRemainingSessionsEstimate:
    def test_estima_atendimentos_pelo_ticket_medio_recente(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
            average_ticket_recent=D("100.00"),
        )
        # Falta R$ 200 (800 - 600) pra cobrir; ticket médio recente R$ 100 -> 2 atendimentos
        assert result.breakeven_remaining_sessions_estimate == 2

    def test_arredonda_para_cima_quando_nao_fecha_exato(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
            average_ticket_recent=D("150.00"),
        )
        # Falta R$ 200; ticket médio R$ 150 -> 1.33... atendimentos -> arredonda pra 2
        assert result.breakeven_remaining_sessions_estimate == 2

    def test_sem_historico_de_ticket_medio_e_none(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
            average_ticket_recent=None,
        )
        assert result.breakeven_remaining_sessions_estimate is None

    def test_ja_bateu_o_breakeven_estimativa_e_zero(self) -> None:
        result = build_dashboard(
            sales=[_sale("2000.00", "1200.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
            average_ticket_recent=D("100.00"),
        )
        assert result.breakeven_remaining_sessions_estimate == 0

    def test_ja_bateu_o_breakeven_e_zero_mesmo_sem_historico_de_ticket_medio(self) -> None:
        result = build_dashboard(
            sales=[_sale("2000.00", "1200.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 15),
            date_to=date(2026, 3, 15),
            has_any_sale_ever=True,
            average_ticket_recent=None,
        )
        assert result.breakeven_remaining_sessions_estimate == 0


class TestBreakevenAlert:
    """Alerta só faz sentido no MÊS CORRENTE em andamento (date_to ==
    today) a poucos dias do fechamento — nunca em "mês passado", que
    também é PeriodKind.MONTH mas com date_to no passado."""

    def test_alerta_ativo_a_5_dias_do_fim_do_mes_sem_bater_breakeven(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 27),  # março tem 31 dias -> faltam 4
            date_to=date(2026, 3, 27),
            has_any_sale_ever=True,
        )
        assert result.breakeven_alert is True

    def test_sem_alerta_quando_faltam_mais_de_5_dias(self) -> None:
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 20),  # faltam 11 dias
            date_to=date(2026, 3, 20),
            has_any_sale_ever=True,
        )
        assert result.breakeven_alert is False

    def test_sem_alerta_quando_ja_bateu_o_breakeven(self) -> None:
        result = build_dashboard(
            sales=[_sale("2000.00", "1200.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 27),
            date_to=date(2026, 3, 27),
            has_any_sale_ever=True,
        )
        assert result.breakeven_alert is False

    def test_sem_alerta_em_mes_passado_mesmo_perto_do_fim_do_periodo(self) -> None:
        # "Mês passado" (last_month): date_to fica fixo no último dia do
        # mês anterior — não é o mês corrente, o alerta não se aplica.
        result = build_dashboard(
            sales=[_sale("1000.00", "600.00")],
            session_count=1,
            fixed_expenses=[_expense("800.00")],
            period_kind=PeriodKind.MONTH,
            today=date(2026, 3, 27),
            date_to=date(2026, 2, 28),
            has_any_sale_ever=True,
        )
        assert result.breakeven_alert is False


class TestCalculateRecentAverageTicket:
    """Base para a estimativa de atendimentos (I7): ticket médio dos
    últimos meses FECHADOS, não do mês corrente (que fica enviesado
    nos primeiros dias)."""

    def test_media_do_faturamento_bruto_sobre_numero_de_vendas(self) -> None:
        sales = [_sale("100.00", "60.00"), _sale("300.00", "180.00")]
        assert calculate_recent_average_ticket(sales) == D("200.00")

    def test_sem_vendas_no_periodo_e_none(self) -> None:
        assert calculate_recent_average_ticket([]) is None


class TestLastNClosedMonthsRange:
    """Janela usada para buscar as vendas que alimentam o ticket médio
    recente — meses FECHADOS, nunca o corrente."""

    def test_janeiro_de_3_meses_fechados_a_partir_de_marco(self) -> None:
        from app.domain.financial.period import last_n_closed_months_range

        date_from, date_to = last_n_closed_months_range(date(2026, 3, 15), n=3)
        assert date_from == date(2025, 12, 1)
        assert date_to == date(2026, 2, 28)

    def test_funciona_na_virada_de_ano(self) -> None:
        from app.domain.financial.period import last_n_closed_months_range

        date_from, date_to = last_n_closed_months_range(date(2026, 1, 20), n=3)
        assert date_from == date(2025, 10, 1)
        assert date_to == date(2025, 12, 31)
