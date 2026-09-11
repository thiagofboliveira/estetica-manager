from uuid import UUID

from app.models.loyalty import LoyaltyTransaction
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
