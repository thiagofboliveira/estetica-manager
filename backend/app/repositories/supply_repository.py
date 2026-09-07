from uuid import UUID

from sqlalchemy import or_

from app.models.supply import Supply, SupplyCategory, SupplyMovement
from app.repositories.base import TenantRepository


class SupplyRepository(TenantRepository[Supply]):
    model = Supply

    def list_all_active(
        self,
        category: SupplyCategory | None = None,
        search: str | None = None,
    ) -> list[Supply]:
        stmt = self._scoped().where(Supply.is_active.is_(True))
        if category:
            stmt = stmt.where(Supply.category == category)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Supply.name.ilike(pattern),
                    Supply.brand.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Supply.name.asc())
        return list(self._session.scalars(stmt).unique())

    def get_by_id(self, supply_id: UUID) -> Supply | None:
        stmt = self._scoped().where(
            Supply.id == supply_id,
            Supply.is_active.is_(True),
        )
        return self._session.scalars(stmt).unique().one_or_none()

    def list_movements(
        self,
        supply_id: UUID | None = None,
        limit: int = 100,
    ) -> list[SupplyMovement]:
        stmt = (
            self._scoped_for(SupplyMovement)
            .order_by(SupplyMovement.created_at.desc())
            .limit(limit)
        )
        if supply_id:
            stmt = stmt.where(SupplyMovement.supply_id == supply_id)
        return list(self._session.scalars(stmt).unique())

    def add_movement(self, movement: SupplyMovement) -> SupplyMovement:
        self._session.add(movement)
        return movement
