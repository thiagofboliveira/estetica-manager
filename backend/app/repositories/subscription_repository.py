from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription import Subscription


class SubscriptionRepository:
    """Repositório de assinaturas do SaaS por clínica."""

    def __init__(self, session: Session, clinic_id: UUID | None = None) -> None:
        self._session = session
        self._clinic_id = clinic_id

    def get_by_clinic_id(self, clinic_id: UUID) -> Subscription | None:
        if self._clinic_id is not None and self._clinic_id != clinic_id:
            return None
        return self._session.scalars(
            select(Subscription).where(Subscription.clinic_id == clinic_id)
        ).one_or_none()

    def get_by_asaas_subscription_id(self, asaas_sub_id: str) -> Subscription | None:
        stmt = select(Subscription).where(
            Subscription.asaas_subscription_id == asaas_sub_id.strip()
        )
        if self._clinic_id is not None:
            stmt = stmt.where(Subscription.clinic_id == self._clinic_id)
        return self._session.scalars(stmt).one_or_none()

    def get_by_asaas_customer_id(self, customer_id: str) -> Subscription | None:
        stmt = select(Subscription).where(
            Subscription.asaas_customer_id == customer_id.strip()
        )
        if self._clinic_id is not None:
            stmt = stmt.where(Subscription.clinic_id == self._clinic_id)
        return self._session.scalars(stmt).one_or_none()

    def add(self, subscription: Subscription) -> Subscription:
        self._session.add(subscription)
        self._session.flush()
        return subscription

    def flush(self) -> None:
        self._session.flush()
