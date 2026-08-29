"""Testes de app/core/money.py — o núcleo do produto.

Puros, sem banco. Um erro aqui é não-retrofitável: os valores de venda
são congelados no snapshot e não podem ser recalculados depois.
"""

from decimal import Decimal as D

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.core.money import allocate, apply_rate, money


class TestMoney:
    def test_normaliza_para_duas_casas(self):
        assert money("10.5") == D("10.50")
        assert money("10") == D("10.00")

    def test_arredonda_half_up_nao_banker(self):
        # Half-up: 0.125 -> 0.13 (não 0.12, que seria banker's rounding,
        # o default do decimal.Decimal.__round__ do Python).
        assert money(D("0.125")) == D("0.13")
        assert money(D("0.135")) == D("0.14")

    def test_rejeita_float(self):
        with pytest.raises(TypeError):
            money(0.1)  # type: ignore[arg-type]

    def test_rejeita_valor_invalido(self):
        with pytest.raises(ValueError):
            money("abc")

    def test_negativo_permitido_para_estorno(self):
        assert money("-50.00") == D("-50.00")


class TestApplyRate:
    def test_aplica_taxa_simples(self):
        assert apply_rate(D("1000.00"), D("0.0399")) == D("39.90")

    def test_arredonda_uma_vez_no_fim(self):
        # 333.33 * 0.10 = 33.333 -> half-up -> 33.33
        assert apply_rate(D("333.33"), D("0.10")) == D("33.33")


class TestAllocate:
    def test_soma_fecha_exatamente_caso_indivisivel(self):
        # R$ 10 entre 3 itens iguais -> 3.34 + 3.33 + 3.33 = 10.00
        result = allocate(D("10.00"), [D("100.00"), D("100.00"), D("100.00")])
        assert sum(result) == D("10.00")
        assert result == [D("3.34"), D("3.33"), D("3.33")]

    def test_proporcional_a_pesos_diferentes(self):
        # Pacote: limpezas R$1000 + peelings R$800, desconto de R$300
        result = allocate(D("300.00"), [D("1000.00"), D("800.00")])
        assert sum(result) == D("300.00")
        # limpezas ~55.6%, peelings ~44.4% de 300
        assert result[0] > result[1]

    def test_peso_zero_divide_igualmente(self):
        result = allocate(D("10.00"), [D("0"), D("0"), D("0")])
        assert sum(result) == D("10.00")

    def test_lista_vazia(self):
        assert allocate(D("10.00"), []) == []

    def test_estorno_negativo_fecha_com_mesmo_sinal(self):
        result = allocate(D("-10.00"), [D("100.00"), D("100.00"), D("100.00")])
        assert sum(result) == D("-10.00")
        assert all(r <= 0 for r in result)

    def test_item_unico_recebe_o_total(self):
        result = allocate(D("50.00"), [D("200.00")])
        assert result == [D("50.00")]

    def test_determinismo(self):
        weights = [D("333.33"), D("333.33"), D("333.34")]
        r1 = allocate(D("100.00"), weights)
        r2 = allocate(D("100.00"), weights)
        assert r1 == r2

    @pytest.mark.parametrize(
        "desconto", ["0.01", "0.02", "0.10", "33.33", "99.99"]
    )
    def test_descontos_indivisiveis_sempre_fecham(self, desconto):
        result = allocate(D(desconto), [D("100.00")] * 3)
        assert sum(result) == D(desconto)


class TestAllocateProperty:
    @given(
        valores=st.lists(
            st.decimals(
                min_value=D("0.01"), max_value=D("10000"), places=2
            ),
            min_size=1,
            max_size=12,
        ),
        frac_desconto=st.decimals(
            min_value=D("0"), max_value=D("1"), places=4
        ),
    )
    def test_rateio_sempre_fecha_para_qualquer_entrada(
        self, valores: list[D], frac_desconto: D
    ):
        total = money(sum(valores))
        desconto = money(total * frac_desconto)
        parcelas = allocate(desconto, valores)
        assert sum(parcelas) == desconto
        assert len(parcelas) == len(valores)
