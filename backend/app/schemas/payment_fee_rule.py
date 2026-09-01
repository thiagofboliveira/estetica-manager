from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.financial_settings import PaymentMethod
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class PaymentFeeRuleCreate(InputSchema):
    payment_method: PaymentMethod
    installments_min: int = Field(ge=1, default=1)
    installments_max: int = Field(ge=1, default=1)
    fee_percentage: str = Field(description="Percentual, ex: '3.20'")
    fixed_fee: str = Field(default="0.00", description="Taxa fixa por transação")


class PaymentFeeRuleUpdate(InputSchema):
    payment_method: PaymentMethod | None = None
    installments_min: int | None = Field(default=None, ge=1)
    installments_max: int | None = Field(default=None, ge=1)
    fee_percentage: str | None = None
    fixed_fee: str | None = None


class PaymentFeeRuleOut(OutputSchema):
    id: UUID
    payment_method: PaymentMethod
    installments_min: int
    installments_max: int
    fee_percentage: MoneyOut
    fixed_fee: MoneyOut
    created_at: datetime
    updated_at: datetime
