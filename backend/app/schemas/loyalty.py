from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import InputSchema, OutputSchema


class LoyaltyTransactionOut(OutputSchema):
    id: UUID
    patient_id: UUID
    sale_id: UUID | None = None
    transaction_type: str
    points: int
    balance_after: int
    description: str
    created_at: datetime | None = None


class LoyaltyAdjustRequest(InputSchema):
    points: int = Field(description="Quantidade de pontos (positivo para crédito, negativo para resgate/débito)")
    description: str = Field(min_length=3, max_length=255, description="Motivo do ajuste ou resgate")
    transaction_type: str = Field(default="ADJUSTMENT", description="ADJUSTMENT, REDEEMED, ou BONUS")


class LoyaltyPatientOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    loyalty_points: int
    vip_tier: str
    vip_badge: str
    monetary_value: Decimal
    referral_code: str
    referred_by_name: str | None = None
    transactions: list[LoyaltyTransactionOut] = Field(default_factory=list)


class ReferralFriendOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    joined_at: datetime
    has_completed_sale: bool


class ReferralInfoOut(OutputSchema):
    referral_code: str
    whatsapp_share_text: str
    whatsapp_share_url: str
    reward_points_per_friend: int
    total_friends_referred: int
    friends_converted_count: int
    total_points_earned_from_referrals: int
    friends: list[ReferralFriendOut] = Field(default_factory=list)


class LoyaltyOverviewOut(OutputSchema):
    total_active_points: int
    total_value_in_currency: Decimal
    tier_counts: dict[str, int]
    total_referrals_count: int
    total_converted_referrals: int
