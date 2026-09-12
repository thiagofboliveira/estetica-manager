from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loyalty import LoyaltyReward, LoyaltyTransaction
from app.repositories.base import TenantRepository


class LoyaltyRepository(TenantRepository[LoyaltyTransaction]):
    model = LoyaltyTransaction

    def list_for_patient(self, patient_id: UUID, limit: int = 50) -> list[LoyaltyTransaction]:
        stmt = (
            self._scoped()
            .where(LoyaltyTransaction.patient_id == patient_id)
            .order_by(LoyaltyTransaction.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def add_transaction(
        self,
        patient_id: UUID,
        points: int,
        balance_after: int,
        transaction_type: str,
        description: str,
        sale_id: UUID | None = None,
    ) -> LoyaltyTransaction:
        tx = LoyaltyTransaction(
            professional_id=self._professional_id,
            patient_id=patient_id,
            sale_id=sale_id,
            transaction_type=transaction_type,
            points=points,
            balance_after=balance_after,
            description=description,
        )
        return self.add(tx)


class LoyaltyRewardRepository(TenantRepository[LoyaltyReward]):
    model = LoyaltyReward

    def list_all(self) -> list[LoyaltyReward]:
        stmt = self._scoped().order_by(LoyaltyReward.order_index.asc(), LoyaltyReward.points_cost.asc())
        return list(self._session.scalars(stmt))

    def list_active(self) -> list[LoyaltyReward]:
        stmt = (
            self._scoped()
            .where(LoyaltyReward.is_active.is_(True))
            .order_by(LoyaltyReward.order_index.asc(), LoyaltyReward.points_cost.asc())
        )
        return list(self._session.scalars(stmt))

    def get_by_id(self, reward_id: UUID) -> LoyaltyReward | None:
        stmt = self._scoped().where(LoyaltyReward.id == reward_id)
        return self._session.scalars(stmt).first()

    @classmethod
    def list_active_by_professional_unscoped(
        cls, session: Session, professional_id: UUID
    ) -> list[LoyaltyReward]:
        stmt = (
            select(LoyaltyReward)
            .where(
                LoyaltyReward.professional_id == professional_id,
                LoyaltyReward.is_active.is_(True),
            )
            .order_by(LoyaltyReward.order_index.asc(), LoyaltyReward.points_cost.asc())
        )
        return list(session.scalars(stmt))

