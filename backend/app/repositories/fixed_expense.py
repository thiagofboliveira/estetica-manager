from app.models.fixed_expense import FixedExpense
from app.repositories.base import TenantRepository


class FixedExpenseRepository(TenantRepository[FixedExpense]):
    model = FixedExpense

    def list_active(self) -> list[FixedExpense]:
        """Vigentes hoje (active_to nulo ou no futuro)."""
        stmt = (
            self._scoped()
            .where(FixedExpense.active_to.is_(None))
            .order_by(FixedExpense.label)
        )
        return list(self._session.scalars(stmt))

    def list_all(self) -> list[FixedExpense]:
        stmt = self._scoped().order_by(FixedExpense.active_from.desc())
        return list(self._session.scalars(stmt))
