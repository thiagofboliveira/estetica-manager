from sqlalchemy import func, select

from app.models.procedure import Procedure, SessionPlan
from app.repositories.base import TenantRepository


class ProcedureRepository(TenantRepository[Procedure]):
    model = Procedure

    def _filtered(self, is_invasive: bool | None, session_plan: SessionPlan | None):
        """Base de SELECT compartilhada por list() e count() — mesmo
        filtro de ativos/atributos, para a contagem bater com a
        listagem."""
        stmt = self._scoped().where(Procedure.is_active.is_(True))
        if is_invasive is not None:
            stmt = stmt.where(Procedure.is_invasive.is_(is_invasive))
        if session_plan is not None:
            stmt = stmt.where(Procedure.session_plan == session_plan)
        return stmt

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        is_invasive: bool | None = None,
        session_plan: SessionPlan | None = None,
    ) -> list[Procedure]:
        stmt = (
            self._filtered(is_invasive, session_plan)
            .order_by(Procedure.name)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))

    def count(
        self, *, is_invasive: bool | None = None, session_plan: SessionPlan | None = None
    ) -> int:
        stmt = select(func.count()).select_from(
            self._filtered(is_invasive, session_plan).subquery()
        )
        return self._session.scalar(stmt) or 0

    def find_by_name(self, name: str) -> Procedure | None:
        """Busca procedimento ativo por nome (case-insensitive) (TASK-BACK-S2-19)."""
        stmt = self._scoped().where(
            func.lower(Procedure.name) == name.strip().lower(),
            Procedure.is_active.is_(True),
        )
        return self._session.scalar(stmt)
