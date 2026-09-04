"""ExpensesByCategoryService — orquestra GET /reports/expenses-by-category.

Camada de orquestração (backend/ENGENHARIA.md §5): busca despesas fixas
vigentes, monta os dataclasses puros de domain/financial/dashboard.py e
chama build_expenses_by_category(). O CÁLCULO em si vive em domain/.
"""

from app.domain.financial.dashboard import FixedExpenseForDashboard
from app.domain.financial.expenses_by_category import (
    ExpenseByCategoryRow,
    build_expenses_by_category,
)
from app.repositories.fixed_expense import FixedExpenseRepository


class ExpensesByCategoryService:
    def __init__(self, fixed_expense_repo: FixedExpenseRepository) -> None:
        self._fixed_expenses = fixed_expense_repo

    def get_breakdown(self) -> list[ExpenseByCategoryRow]:
        expenses = [
            FixedExpenseForDashboard(
                amount=e.amount,
                periodicity=e.periodicity.value,
                category=e.category,
            )
            for e in self._fixed_expenses.list_active()
        ]
        return build_expenses_by_category(expenses)
