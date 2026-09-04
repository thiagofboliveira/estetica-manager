"""Despesas por categoria (gráfico "despesas correntes por tipo") — puro, sem banco."""

from decimal import Decimal as D

from app.domain.financial.dashboard import FixedExpenseForDashboard
from app.domain.financial.expenses_by_category import (
    SEM_CATEGORIA,
    build_expenses_by_category,
)


def test_agrupa_por_categoria_somando_despesas_mensais() -> None:
    expenses = [
        FixedExpenseForDashboard(amount=D("800.00"), periodicity="MONTHLY", category="aluguel"),
        FixedExpenseForDashboard(amount=D("400.00"), periodicity="MONTHLY", category="aluguel"),
        FixedExpenseForDashboard(amount=D("150.00"), periodicity="MONTHLY", category="água/luz"),
    ]
    rows = build_expenses_by_category(expenses)
    assert len(rows) == 2
    assert rows[0].category == "aluguel"
    assert rows[0].monthly_amount == D("1200.00")
    assert rows[1].category == "água/luz"
    assert rows[1].monthly_amount == D("150.00")


def test_despesa_sem_categoria_vira_balde_sem_categoria() -> None:
    expenses = [
        FixedExpenseForDashboard(amount=D("100.00"), periodicity="MONTHLY", category=None),
        FixedExpenseForDashboard(amount=D("50.00"), periodicity="MONTHLY", category="  "),
    ]
    rows = build_expenses_by_category(expenses)
    assert len(rows) == 1
    assert rows[0].category == SEM_CATEGORIA
    assert rows[0].monthly_amount == D("150.00")


def test_despesa_yearly_entra_ratada_por_12() -> None:
    # Taxa de vigilância sanitária: R$1200/ano -> R$100/mês (MVP v7.1 §12.5).
    expenses = [
        FixedExpenseForDashboard(
            amount=D("1200.00"), periodicity="YEARLY", category="taxas"
        ),
    ]
    rows = build_expenses_by_category(expenses)
    assert rows[0].monthly_amount == D("100.00")


def test_ordenado_por_valor_mensal_decrescente() -> None:
    expenses = [
        FixedExpenseForDashboard(amount=D("50.00"), periodicity="MONTHLY", category="pequena"),
        FixedExpenseForDashboard(amount=D("900.00"), periodicity="MONTHLY", category="grande"),
    ]
    rows = build_expenses_by_category(expenses)
    assert [r.category for r in rows] == ["grande", "pequena"]


def test_lista_vazia_nao_quebra() -> None:
    assert build_expenses_by_category([]) == []
