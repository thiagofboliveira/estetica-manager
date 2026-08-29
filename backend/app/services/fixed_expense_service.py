from datetime import date
from uuid import UUID

from app.core.money import money
from app.models.fixed_expense import FixedExpense
from app.repositories.fixed_expense import FixedExpenseRepository
from app.schemas.fixed_expense import FixedExpenseCreate, FixedExpenseUpdate


class FixedExpenseNotFoundError(Exception):
    pass


class FixedExpenseService:
    def __init__(self, repo: FixedExpenseRepository) -> None:
        self._repo = repo

    def create(self, dto: FixedExpenseCreate) -> FixedExpense:
        expense = FixedExpense(
            label=dto.label,
            category=dto.category,
            amount=money(dto.amount),
            periodicity=dto.periodicity,
            active_from=dto.active_from,
        )
        return self._repo.add(expense)

    def get(self, expense_id: UUID) -> FixedExpense:
        expense = self._repo.get(expense_id)
        if expense is None:
            raise FixedExpenseNotFoundError()
        return expense

    def list_active(self) -> list[FixedExpense]:
        return self._repo.list_active()

    def list_all(self) -> list[FixedExpense]:
        return self._repo.list_all()

    def update(self, expense_id: UUID, dto: FixedExpenseUpdate) -> FixedExpense:
        expense = self.get(expense_id)
        data = dto.model_dump(exclude_unset=True)

        if "amount" in data and data["amount"] is not None:
            data["amount"] = money(data["amount"])

        for field, value in data.items():
            setattr(expense, field, value)

        self._repo.flush()
        return expense

    def archive(self, expense_id: UUID) -> None:
        """Fecha a vigência (active_to=hoje) — nunca hard delete, mesmo
        princípio de patients.is_active (MVP v6 §10). Preserva o
        histórico de quanto ela gastava em meses passados."""
        expense = self.get(expense_id)
        expense.active_to = date.today()
        self._repo.flush()
