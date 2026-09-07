from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.vial import VialStatus
from app.schemas.base import InputSchema, OutputSchema


class OpenVialCreate(InputSchema):
    medication_name: str = Field(
        default="Toxina Botulínica", min_length=2, max_length=255
    )
    lot_number: str | None = Field(default=None, max_length=100)
    total_units: Decimal = Field(default=Decimal("100.00"), gt=0)
    used_units: Decimal = Field(default=Decimal("0.00"), ge=0)
    unit_measure: str = Field(default="U", max_length=20)
    cost_price: Decimal | None = Field(default=None, ge=0)
    opened_at: datetime | None = None
    expires_at: datetime | None = None
    validity_days: int = Field(
        default=30, ge=1, le=365, description="Dias de validade na geladeira (padrão: 30)"
    )
    procedure_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)


class OpenVialConsume(InputSchema):
    units: Decimal = Field(gt=0, description="Quantidade de unidades consumidas nesta aplicação")
    patient_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=255)


class OpenVialUpdate(InputSchema):
    medication_name: str | None = Field(default=None, min_length=2, max_length=255)
    lot_number: str | None = None
    status: VialStatus | None = None
    cost_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class OpenVialOut(OutputSchema):
    id: UUID
    medication_name: str
    lot_number: str | None = None
    total_units: Decimal
    used_units: Decimal
    remaining_units: Decimal
    unit_measure: str
    cost_price: Decimal | None = None
    cost_per_unit: Decimal | None = None
    estimated_loss_risk: Decimal | None = None
    opened_at: datetime
    expires_at: datetime
    days_remaining: int
    is_expired: bool
    status: VialStatus
    procedure_id: UUID | None = None
    procedure_name: str | None = None
    notes: str | None = None
    created_at: datetime
