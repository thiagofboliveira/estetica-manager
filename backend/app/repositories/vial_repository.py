from uuid import UUID

from sqlalchemy.orm import joinedload

from app.models.vial import OpenVial, VialStatus
from app.repositories.base import TenantRepository


class OpenVialRepository(TenantRepository[OpenVial]):
    model = OpenVial

    def list_active(self) -> list[OpenVial]:
        stmt = (
            self._scoped()
            .options(joinedload(OpenVial.procedure))
            .where(
                OpenVial.status == VialStatus.OPEN,
                OpenVial.is_active.is_(True),
            )
            .order_by(OpenVial.expires_at.asc())
        )
        return list(self._session.scalars(stmt).unique())

    def list_recent(self, limit: int = 50) -> list[OpenVial]:
        stmt = (
            self._scoped()
            .options(joinedload(OpenVial.procedure))
            .where(OpenVial.is_active.is_(True))
            .order_by(OpenVial.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).unique())

    def get_with_procedure(self, vial_id: UUID) -> OpenVial | None:
        stmt = (
            self._scoped()
            .options(joinedload(OpenVial.procedure))
            .where(
                OpenVial.id == vial_id,
                OpenVial.is_active.is_(True),
            )
        )
        return self._session.scalars(stmt).unique().one_or_none()
