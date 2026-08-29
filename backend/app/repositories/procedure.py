from app.models.procedure import Procedure
from app.repositories.base import TenantRepository


class ProcedureRepository(TenantRepository[Procedure]):
    model = Procedure

    def list(self, *, limit: int = 50, offset: int = 0) -> list[Procedure]:
        stmt = (
            self._scoped()
            .where(Procedure.is_active.is_(True))
            .order_by(Procedure.name)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))
