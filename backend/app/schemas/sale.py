from datetime import date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.models.financial_settings import FeePayer, PaymentMethod, SplitBase
from app.models.sale import SaleStatus, SaleType
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut, RateOut


class SaleItemCreate(InputSchema):
    procedure_id: UUID
    quantity: int = Field(ge=1)


class SaleCreate(InputSchema):
    patient_id: UUID
    type: SaleType
    items: list[SaleItemCreate] = Field(min_length=1)
    discount_amount: str = Field(default="0.00")
    payment_method: PaymentMethod
    installments: int = Field(default=1, ge=1)
    notes: str | None = None
    booking_id: UUID | None = None

    @model_validator(mode="after")
    def _pacote_pre_pago(self) -> "SaleCreate":
        # "PACKAGE significa pré-pago" (§11.2) — não há regra adicional
        # de validação aqui além da existente (venda sempre à vista no
        # sentido de "já paga"); type só direciona PENDING vs SCHEDULED
        # na geração de sessões.
        return self


class SaleItemOut(OutputSchema):
    id: UUID
    procedure_id: UUID
    quantity: int
    unit_price: MoneyOut
    unit_cost_estimated: MoneyOut
    return_interval_applied: int | None
    discount_allocated: MoneyOut


class SessionOut(OutputSchema):
    id: UUID
    sale_item_id: UUID
    sequence_number: int
    scheduled_at: datetime | None
    status: str
    modality: str


class SaleOut(OutputSchema):
    id: UUID
    patient_id: UUID
    type: SaleType
    sold_at: date
    status: SaleStatus

    payment_method: PaymentMethod
    installments: int

    items_total: MoneyOut
    discount_amount: MoneyOut
    gross_amount: MoneyOut

    split_applied: RateOut
    split_base_applied: SplitBase
    fee_payer_applied: FeePayer
    fee_applied: RateOut
    fee_amount_applied: MoneyOut

    cost_provisioned: MoneyOut
    cost_realized: MoneyOut

    net_profit: MoneyOut
    margin: RateOut | None
    expected_receipt_date: date | None

    notes: str | None
    created_at: datetime
    updated_at: datetime

    items: list[SaleItemOut] = Field(default_factory=list)
    sessions: list[SessionOut] = Field(default_factory=list)
