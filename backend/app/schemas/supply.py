from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.supply import MovementType, SupplyCategory
from app.schemas.base import InputSchema, OutputSchema


class SupplyCreate(InputSchema):
    name: str = Field(min_length=2, max_length=255)
    category: SupplyCategory = Field(default=SupplyCategory.CONSUMABLE)
    brand: str | None = Field(default=None, max_length=100)
    unit_measure: str = Field(default="UN", max_length=30)
    current_stock: Decimal = Field(default=Decimal("0.00"), ge=0)
    min_stock_alert: Decimal | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class SupplyUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    category: SupplyCategory | None = None
    brand: str | None = Field(default=None, max_length=100)
    unit_measure: str | None = Field(default=None, max_length=30)
    current_stock: Decimal | None = Field(default=None, ge=0)
    min_stock_alert: Decimal | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class SupplyMovementCreate(InputSchema):
    movement_type: MovementType
    quantity: Decimal = Field(gt=0, description="Quantidade a ser movimentada")
    unit_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class SupplyMovementOut(OutputSchema):
    id: UUID
    supply_id: UUID
    movement_type: MovementType
    quantity: Decimal
    unit_price: Decimal | None = None
    notes: str | None = None
    created_at: datetime


class SupplyOut(OutputSchema):
    id: UUID
    name: str
    category: SupplyCategory
    brand: str | None = None
    unit_measure: str
    current_stock: Decimal
    min_stock_alert: Decimal | None = None
    cost_price: Decimal | None = None
    notes: str | None = None
    is_active: bool
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime
