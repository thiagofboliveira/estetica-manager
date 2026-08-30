"""Matriz de 5 configurações do motor de lucro (MVP v6 TASK-044, a fonte
de verdade oficial — não o texto narrativo de exemplo em §12, que usa
uma fórmula ligeiramente diferente para descrever "Modelo D").

Cenário base: R$1000, split 30%, taxa 5%, custo R$300.

  A — GROSS,       PROFESSIONAL   -> R$350
  B — NET_OF_FEE,  PROFESSIONAL   -> R$365
  C — GROSS,       SPLIT_PRO_RATA -> R$365
  D — GROSS,       CLINIC         -> R$400
  E — GROSS,       PROFESSIONAL, split 0% (autônoma sem clínica) -> R$650

Puro: sem banco, sem FastAPI — roda em milissegundos
(backend/ENGENHARIA.md §5/§6).
"""

from datetime import date
from decimal import Decimal as D

import pytest

from app.core.money import ZERO, allocate
from app.domain.financial.calculator import (
    FeePayer,
    FeeRule,
    LineItem,
    PaymentMethod,
    SaleParams,
    SplitBase,
    calculate_sale,
    expected_receipt_date,
)


def _base_item(cost: str = "300.00") -> LineItem:
    return LineItem(
        unit_price=D("1000.00"),
        quantity=1,
        unit_cost_estimated=D(cost),
        session_costs=[D(cost)],
    )


def _params(
    split_pct: str, split_base: SplitBase, fee_payer: FeePayer, fee_pct: str = "5.00"
) -> SaleParams:
    return SaleParams(
        split_clinic_percentage=D(split_pct),
        split_base=split_base,
        fee_payer=fee_payer,
        payment_method=PaymentMethod.CREDIT,
        installments=1,
        discount_amount=ZERO,
        fee_rules=[FeeRule(1, 1, D(fee_pct))],
    )


MATRIX = {
    "A_gross_professional": (
        _params("30.00", SplitBase.GROSS, FeePayer.PROFESSIONAL),
        D("350.00"),
    ),
    "B_net_of_fee_professional": (
        _params("30.00", SplitBase.NET_OF_FEE, FeePayer.PROFESSIONAL),
        D("365.00"),
    ),
    "C_gross_split_pro_rata": (
        _params("30.00", SplitBase.GROSS, FeePayer.SPLIT_PRO_RATA),
        D("365.00"),
    ),
    "D_gross_clinic": (
        _params("30.00", SplitBase.GROSS, FeePayer.CLINIC),
        D("400.00"),
    ),
    "E_sem_split": (
        _params("0.00", SplitBase.GROSS, FeePayer.PROFESSIONAL),
        D("650.00"),
    ),
}


@pytest.mark.parametrize(
    "params,expected_profit", MATRIX.values(), ids=list(MATRIX.keys())
)
def test_matriz_de_5_configuracoes(params: SaleParams, expected_profit: D) -> None:
    result = calculate_sale([_base_item()], params)
    assert result.net_profit == expected_profit


@pytest.mark.parametrize("params,_", MATRIX.values(), ids=list(MATRIX.keys()))
class TestInvariantesUniversais:
    """Valem em TODAS as 5 configurações (backend/ENGENHARIA.md §6)."""

    def test_soma_dos_itens_de_desconto_fecha_com_o_total(
        self, params: SaleParams, _: D
    ) -> None:
        items = [
            LineItem(D("250.00"), 4, D("50.00"), [D("50.00")] * 4),
            LineItem(D("400.00"), 2, D("80.00"), [D("80.00")] * 2),
        ]
        params_with_discount = SaleParams(
            split_clinic_percentage=params.split_clinic_percentage,
            split_base=params.split_base,
            fee_payer=params.fee_payer,
            payment_method=params.payment_method,
            installments=params.installments,
            discount_amount=D("300.00"),
            fee_rules=params.fee_rules,
        )
        result = calculate_sale(items, params_with_discount)
        assert sum(i.discount_allocated for i in result.items) == D("300.00")

    def test_identidade_contabil_gross_e_items_menos_desconto(
        self, params: SaleParams, _: D
    ) -> None:
        result = calculate_sale([_base_item()], params)
        assert result.gross_amount == result.items_total - result.discount_amount

    def test_tudo_tem_duas_casas(self, params: SaleParams, _: D) -> None:
        result = calculate_sale([_base_item()], params)
        for value in (
            result.items_total,
            result.gross_amount,
            result.fee_amount,
            result.split_amount,
            result.cost_provisioned,
            result.cost_realized,
            result.net_profit,
        ):
            assert value == value.quantize(D("0.01"))

    def test_determinismo(self, params: SaleParams, _: D) -> None:
        r1 = calculate_sale([_base_item()], params)
        r2 = calculate_sale([_base_item()], params)
        assert r1.net_profit == r2.net_profit
        assert r1.split_amount == r2.split_amount
        assert r1.fee_amount == r2.fee_amount


@pytest.mark.parametrize("desconto", ["0.01", "0.10", "33.33", "99.99"])
def test_rateio_indivisivel_sempre_fecha(desconto: str) -> None:
    weights = [D("250.00"), D("400.00"), D("350.00")]
    result = allocate(D(desconto), weights)
    assert sum(result) == D(desconto)


def test_margem_none_quando_bruto_zero() -> None:
    item = LineItem(D("0.00"), 1, D("0.00"), [D("0.00")])
    params = _params("30.00", SplitBase.GROSS, FeePayer.PROFESSIONAL, fee_pct="0.00")
    result = calculate_sale([item], params)
    assert result.margin is None


def test_margem_negativa_visivel_quando_custo_maior_que_bruto() -> None:
    item = LineItem(D("100.00"), 1, D("500.00"), [D("500.00")])
    params = _params("0.00", SplitBase.GROSS, FeePayer.PROFESSIONAL, fee_pct="0.00")
    result = calculate_sale([item], params)
    assert result.net_profit < ZERO
    assert result.margin is not None
    assert result.margin < ZERO


def test_custo_realizado_menor_que_provisionado_quando_sessao_expira() -> None:
    """§12.1 — sessão EXPIRED libera custo: quem monta o LineItem exclui
    o custo dessa sessão de session_costs, cost_realized cai e o lucro
    sobe em relação ao dia 1."""
    item_dia1 = LineItem(
        unit_price=D("2000.00"),
        quantity=10,
        unit_cost_estimated=D("50.00"),
        session_costs=[D("50.00")] * 10,  # todas ainda pendentes/ativas
    )
    item_pos_expiracao = LineItem(
        unit_price=D("2000.00"),
        quantity=10,
        unit_cost_estimated=D("50.00"),
        # 6 concluídas + 4 expiradas -> só 6 custos contam
        session_costs=[D("50.00")] * 6,
    )
    params = _params("30.00", SplitBase.GROSS, FeePayer.PROFESSIONAL, fee_pct="0.00")

    dia1 = calculate_sale([item_dia1], params)
    pos = calculate_sale([item_pos_expiracao], params)

    assert dia1.cost_provisioned == D("500.00")
    assert dia1.cost_realized == D("500.00")
    assert pos.cost_provisioned == D("500.00")  # provisionado não muda
    assert pos.cost_realized == D("300.00")  # realizado caiu
    assert pos.net_profit > dia1.net_profit  # lucro sobe ao expirar


def test_arredondamento_com_dizima_333_33_vezes_33_porcento() -> None:
    """T-043 — caso clássico de dízima periódica: 333,33 × 33% =
    109,9989, que precisa arredondar (ROUND_HALF_UP) para 110,00, nunca
    109,99 (banker's rounding) nem propagar erro de ponto flutuante."""
    item = LineItem(
        unit_price=D("333.33"),
        quantity=1,
        unit_cost_estimated=D("0.00"),
        session_costs=[D("0.00")],
    )
    params = SaleParams(
        split_clinic_percentage=D("33.00"),
        split_base=SplitBase.GROSS,
        fee_payer=FeePayer.PROFESSIONAL,
        payment_method=PaymentMethod.PIX,
        installments=1,
        discount_amount=ZERO,
        fee_rules=[],
    )
    result = calculate_sale([item], params)
    assert result.split_amount == D("110.00")
    assert result.net_profit == D("223.33")


class TestExpectedReceiptDate:
    """TASK-021 — lucro não é caixa. Teste automatizado obrigatório
    (MVP v7.1) mesmo sem a cliente zero exercitar crédito parcelado."""

    @pytest.mark.parametrize(
        "method",
        [
            PaymentMethod.PIX,
            PaymentMethod.DEBIT,
            PaymentMethod.CASH,
            PaymentMethod.TRANSFER,
        ],
    )
    def test_metodos_a_vista_sao_d_mais_zero(self, method: PaymentMethod) -> None:
        sold_at = date(2026, 8, 29)
        assert expected_receipt_date(method, sold_at, installments=1) == sold_at

    def test_credito_a_vista_e_d_mais_30(self) -> None:
        sold_at = date(2026, 8, 29)
        result = expected_receipt_date(PaymentMethod.CREDIT, sold_at, installments=1)
        assert result == date(2026, 9, 28)

    def test_credito_parcelado_e_d_mais_30_vezes_parcelas(self) -> None:
        sold_at = date(2026, 8, 29)
        result = expected_receipt_date(PaymentMethod.CREDIT, sold_at, installments=10)
        assert result == date(2027, 6, 25)  # 300 dias após 29/08

    def test_credito_12x_data_condiz_com_30_dias_por_parcela(self) -> None:
        sold_at = date(2026, 1, 1)
        result = expected_receipt_date(PaymentMethod.CREDIT, sold_at, installments=12)
        assert (result - sold_at).days == 360
