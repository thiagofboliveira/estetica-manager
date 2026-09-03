from datetime import datetime, time
from uuid import UUID

from app.models.financial_settings import FeePayer, PaymentMethod, SplitBase
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class FinancialSettingsUpdate(InputSchema):
    split_clinic_percentage: str | None = None
    split_base: SplitBase | None = None
    fee_payer: FeePayer | None = None
    pix_fee_percentage: str | None = None
    debit_card_fee_percentage: str | None = None
    default_payment_method: PaymentMethod | None = None
    anticipates_all: bool | None = None
    anticipation_rate_per_installment: str | None = None
    work_start_time: time | None = None
    work_end_time: time | None = None
    slot_duration_minutes: int | None = None
    buffer_minutes: int | None = None


class FinancialSettingsOut(OutputSchema):
    id: UUID
    split_clinic_percentage: MoneyOut
    split_base: SplitBase
    fee_payer: FeePayer
    pix_fee_percentage: MoneyOut
    debit_card_fee_percentage: MoneyOut
    default_payment_method: PaymentMethod
    anticipates_all: bool = False
    anticipation_rate_per_installment: MoneyOut | None = None
    work_start_time: time
    work_end_time: time
    slot_duration_minutes: int
    buffer_minutes: int
    created_at: datetime
    updated_at: datetime
