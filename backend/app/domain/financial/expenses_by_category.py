"""Despesas fixas agrupadas por categoria (gráfico "despesas correntes por tipo").

PURO: sem SQLAlchemy, sem FastAPI (backend/ENGENHARIA.md §5).

`fixed_expenses.category` é texto livre de propósito (models/fixed_expense.py):
a entrevista só trouxe um caso real (aluguel) — inventar uma taxonomia
fechada seria projetar para hipótese, não para necessidade observada
(MVP §32, segundo corolário). Este módulo agrupa pelo texto exatamente
como foi gravado (só normalizado por trim), sem inventar categorias. Se
o padrão de uso mostrar 3-4 categorias repetidas, formaliza-se depois —
mesma decisão já registrada para o campo em si.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.core.money import ZERO, money
from app.domain.financial.dashboard import FixedExpenseForDashboard, monthly_equivalent

SEM_CATEGORIA = "Sem categoria"


@dataclass(frozen=True)
class ExpenseByCategoryRow:
    category: str
    monthly_amount: Decimal


def build_expenses_by_category(
    expenses: list[FixedExpenseForDashboard],
) -> list[ExpenseByCategoryRow]:
    """Cada despesa entra pelo equivalente MENSAL (YEARLY ÷ 12, mesma
    regra do dashboard via monthly_equivalent) — nunca o valor bruto do
    ciclo, senão uma taxa anual pareceria 12x maior que um aluguel
    mensal no gráfico, e o número, embora somado certo, contaria uma
    história errada sobre onde o dinheiro vai todo mês."""
    accumulated: dict[str, Decimal] = {}
    for expense in expenses:
        label = (expense.category or "").strip() or SEM_CATEGORIA
        accumulated[label] = money(accumulated.get(label, ZERO) + monthly_equivalent(expense))

    rows = [
        ExpenseByCategoryRow(category=category, monthly_amount=amount)
        for category, amount in accumulated.items()
    ]
    return sorted(rows, key=lambda r: r.monthly_amount, reverse=True)
