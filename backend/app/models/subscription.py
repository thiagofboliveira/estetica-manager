from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.billing.pricing import BillingCycle
from app.models.base import Base, TimestampMixin


class SubscriptionStatus(str, Enum):
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class Subscription(Base, TimestampMixin):
    """Assinatura do SaaS vinculada à Clínica contratante."""

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    clinic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
    )
    plan_id: Mapped[str] = mapped_column(String(50), default="pro", nullable=False)
    cycle: Mapped[BillingCycle] = mapped_column(
        String(20), default=BillingCycle.MONTHLY, nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(30), default=SubscriptionStatus.TRIALING, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("80.00"), nullable=False
    )
    trial_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    trial_ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    asaas_customer_id: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )
    asaas_subscription_id: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )
    coupon_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("coupons.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    invoice_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pix_qrcode_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    clinic = relationship("Clinic", foreign_keys=[clinic_id])
    coupon = relationship("Coupon", foreign_keys=[coupon_id])
