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


class PublicLoyaltyRewardOut(OutputSchema):
    points_cost: int
    title: str
    description: str
    discount_value: Decimal | None = None


class PublicVipCardOut(OutputSchema):
    patient_first_name: str
    patient_full_name: str
    clinic_name: str
    vip_tier: str
    vip_badge: str
    loyalty_points: int
    monetary_credit_value: Decimal
    next_tier: str | None = None
    points_to_next_tier: int = 0
    next_tier_threshold: int | None = None
    referral_code: str
    referral_whatsapp_message: str
    public_booking_slug: str | None = None
    catalog_rewards: list[PublicLoyaltyRewardOut] = Field(default_factory=list)


class SendVipEmailResponse(OutputSchema):
    success: bool
    message: str
    recipient_email: str


class LoyaltyRewardCreate(InputSchema):
    points_cost: int = Field(ge=1, description="Pontos necessários para resgatar o benefício")
    title: str = Field(min_length=2, max_length=120, description="Nome do benefício/recompensa")
    description: str = Field(default="", max_length=255, description="Descrição detalhada do benefício")
    discount_value: Decimal | None = Field(default=None, ge=0, description="Valor estimado de desconto em R$")
    is_active: bool = Field(default=True, description="Se está disponível no catálogo")
    order_index: int = Field(default=0, ge=0, description="Ordem de exibição no catálogo")


class LoyaltyRewardUpdate(InputSchema):
    points_cost: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    discount_value: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    order_index: int | None = Field(default=None, ge=0)


class LoyaltyRewardOut(OutputSchema):
    id: UUID
    points_cost: int
    title: str
    description: str
    discount_value: Decimal | None = None
    is_active: bool
    order_index: int
    created_at: datetime | None = None


