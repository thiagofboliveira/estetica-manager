"""Schemas Pydantic para Billing, Planos e Assinaturas."""

from datetime import datetime
from pydantic import Field, field_validator

from app.domain.billing.pricing import BillingCycle
from app.schemas.base import InputSchema, OutputSchema


class PlanCycleOut(OutputSchema):
    cycle: BillingCycle
    months: int
    monthly_equivalent: str
    total_amount: str
    savings_percentage: str
    badge: str | None = None
    is_featured: bool = False


class PlanOut(OutputSchema):
    id: str
    name: str
    description: str
    trial_days: int
    is_launch_promo: bool
    promo_headline: str
    promo_badge: str
    features: list[str]
    cycles: list[PlanCycleOut]


class CouponValidateIn(InputSchema):
    code: str = Field(min_length=2, max_length=50)
    cycle: BillingCycle

    @field_validator("cycle", mode="before")
    @classmethod
    def normalize_cycle(cls, v: object) -> object:
        if isinstance(v, str):
            return v.upper()
        return v


class CouponValidateOut(OutputSchema):
    is_valid: bool
    code: str
    discount_type: str | None = None
    original_amount: str
    discount_amount: str
    final_amount: str
    savings_percentage: str
    message: str | None = None


class CheckoutIn(InputSchema):
    cycle: BillingCycle
    coupon_code: str | None = Field(default=None, max_length=50)
    billing_type: str = Field(default="UNDEFINED", description="UNDEFINED, PIX, CREDIT_CARD, BOLETO")
    document: str | None = Field(default=None, max_length=20, description="CPF ou CNPJ para emissão de nota")
    phone: str | None = Field(default=None, max_length=30)

    @field_validator("cycle", mode="before")
    @classmethod
    def normalize_cycle(cls, v: object) -> object:
        if isinstance(v, str):
            return v.upper()
        return v


class CheckoutOut(OutputSchema):
    subscription_id: str
    status: str
    amount: str
    cycle: BillingCycle
    invoice_url: str | None = None
    pix_qrcode_payload: str | None = None
    first_due_date: str
    is_trial_included: bool


class SubscriptionStatusOut(OutputSchema):
    status: str
    plan_id: str
    cycle: BillingCycle
    amount: str
    trial_started_at: datetime
    trial_ends_at: datetime
    days_left_in_trial: int
    is_trial_active: bool
    is_subscription_active: bool
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    invoice_url: str | None = None
