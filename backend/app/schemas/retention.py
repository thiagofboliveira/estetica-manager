from datetime import date, datetime
from uuid import UUID

from app.domain.retention.enums import (
    ContactChannel,
    ReturnOpportunityStatus,
    Timing,
)
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class ReturnOpportunityUpdate(InputSchema):
    status: ReturnOpportunityStatus | None = None
    contact_channel: ContactChannel | None = None
    contact_status: str | None = None
    contacted_at: datetime | None = None
    dismissed: bool | None = None


class OpportunityItemOut(OutputSchema):
    id: UUID
    procedure_id: UUID
    procedure_name: str
    due_date: date
    timing: Timing
    status: ReturnOpportunityStatus
    potential_value: MoneyOut
    days_diff: int


class PatientRetentionCardOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    patient_phone: str | None
    consent_whatsapp: bool
    opted_out: bool
    is_suppressed: bool
    last_contacted_at: datetime | None
    total_potential_value: MoneyOut
    primary_opportunity: OpportunityItemOut
    secondary_opportunities: list[OpportunityItemOut]
    whatsapp_enabled: bool
    disabled_reason: str | None


class ReturnOpportunityOut(OutputSchema):
    id: UUID
    patient_id: UUID
    patient_name: str
    patient_phone: str | None
    procedure_id: UUID
    procedure_name: str
    source_sale_item_id: UUID | None
    due_date: date
    timing: Timing
    status: ReturnOpportunityStatus
    potential_value: MoneyOut
    contacted_at: datetime | None
    contact_channel: ContactChannel | None
    contact_status: str | None
    resolved_by_sale_id: UUID | None
    dismissed_at: datetime | None
    created_at: datetime
    updated_at: datetime
