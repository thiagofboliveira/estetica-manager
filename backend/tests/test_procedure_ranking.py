"""Ranking de procedimentos (MVP v6 §13, TASK-024) — puro, sem banco."""

import uuid
from decimal import Decimal as D

from app.domain.financial.procedure_ranking import (
    ItemForRanking,
    build_procedure_ranking,
)

BOTOX_ID = uuid.uuid4()
LIMPEZA_ID = uuid.uuid4()


def test_venda_avulsa_simples() -> None:
    items = [
        ItemForRanking(
            procedure_id=BOTOX_ID, procedure_name="Botox",
            unit_price=D("1000.00"), quantity=1, unit_cost_estimated=D("300.00"),
            discount_allocated=D("0.00"),
            sale_split_amount=D("300.00"), sale_fee_charged=D("50.00"),
            sale_line_totals_sum=D("1000.00"),
        ),
    ]
    ranking = build_procedure_ranking(items)
    assert len(ranking) == 1
    row = ranking[0]
    assert row.procedure_name == "Botox"
    assert row.gross_revenue == D("1000.00")
    # 1000 - 300(split) - 50(taxa) - 300(custo) = 350, igual ao exemplo do MVP §12.
    assert row.net_profit == D("350.00")
    assert row.margin == D("0.35")


def test_agrupa_por_procedimento_entre_vendas_diferentes() -> None:
    sale_a = ItemForRanking(
        procedure_id=BOTOX_ID, procedure_name="Botox",
        unit_price=D("1000.00"), quantity=1, unit_cost_estimated=D("300.00"),
        discount_allocated=D("0.00"),
        sale_split_amount=D("0.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("1000.00"),
    )
    sale_b = ItemForRanking(
        procedure_id=BOTOX_ID, procedure_name="Botox",
        unit_price=D("1000.00"), quantity=1, unit_cost_estimated=D("300.00"),
        discount_allocated=D("0.00"),
        sale_split_amount=D("100.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("1000.00"),
    )
    ranking = build_procedure_ranking([sale_a, sale_b])
    assert len(ranking) == 1
    assert ranking[0].gross_revenue == D("2000.00")
    assert ranking[0].net_profit == D("1300.00")  # 700 + 600


def test_pacote_com_dois_procedimentos_diferentes_rateio_fecha_com_o_total() -> None:
    # Pacote: 4 limpezas (R$250) + 2 peelings (R$400) = R$1800.
    # Vendido por R$1500 -> desconto R$300 (mesmo exemplo do MVP §11.5).
    limpeza = ItemForRanking(
        procedure_id=LIMPEZA_ID, procedure_name="Limpeza",
        unit_price=D("250.00"), quantity=4, unit_cost_estimated=D("50.00"),
        discount_allocated=D("166.67"),
        sale_split_amount=D("450.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("1800.00"),
    )
    peeling = ItemForRanking(
        procedure_id=BOTOX_ID, procedure_name="Peeling",  # reusando UUID só como id distinto
        unit_price=D("400.00"), quantity=2, unit_cost_estimated=D("80.00"),
        discount_allocated=D("133.33"),
        sale_split_amount=D("450.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("1800.00"),
    )
    ranking = build_procedure_ranking([limpeza, peeling])

    total_revenue = sum((r.gross_revenue for r in ranking), D("0.00"))
    # net_of_discount: limpeza 1000-166.67=833.33, peeling 800-133.33=666.67 -> soma 1500.00
    assert total_revenue == D("1500.00")

    # A soma do lucro dos itens tem que fechar com o que a venda de fato
    # deu: bruto(1500) - split(450, é da VENDA inteira) - custo(4×50+2×80=360)
    total_profit = sum((r.net_profit for r in ranking), D("0.00"))
    assert total_profit == D("1500.00") - D("450.00") - D("360.00")


def test_margem_none_quando_receita_zero() -> None:
    item = ItemForRanking(
        procedure_id=BOTOX_ID, procedure_name="Cortesia",
        unit_price=D("0.00"), quantity=1, unit_cost_estimated=D("0.00"),
        discount_allocated=D("0.00"),
        sale_split_amount=D("0.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("0.00"),
    )
    ranking = build_procedure_ranking([item])
    assert ranking[0].margin is None


def test_ordenado_por_faturamento_decrescente() -> None:
    baixo = ItemForRanking(
        procedure_id=LIMPEZA_ID, procedure_name="Limpeza",
        unit_price=D("100.00"), quantity=1, unit_cost_estimated=D("20.00"),
        discount_allocated=D("0.00"),
        sale_split_amount=D("0.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("100.00"),
    )
    alto = ItemForRanking(
        procedure_id=BOTOX_ID, procedure_name="Botox",
        unit_price=D("1000.00"), quantity=1, unit_cost_estimated=D("300.00"),
        discount_allocated=D("0.00"),
        sale_split_amount=D("0.00"), sale_fee_charged=D("0.00"),
        sale_line_totals_sum=D("1000.00"),
    )
    ranking = build_procedure_ranking([baixo, alto])
    assert [r.procedure_name for r in ranking] == ["Botox", "Limpeza"]
