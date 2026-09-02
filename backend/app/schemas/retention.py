from datetime import date, datetime
from uuid import UUID

from app.models.return_opportunity import ContactChannel, ReturnOpportunityStatus
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class OpportunityLineOut(OutputSchema):
    id: UUID
    procedure: str
    due_date: date
    timing: str
    status: ReturnOpportunityStatus
    potential_value: MoneyOut


class PatientRetentionOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    patient_phone: str | None
    can_contact: bool
    cannot_contact_reason: str | None
    total_potential_value: MoneyOut
    opportunities: list[OpportunityLineOut]


class ReturnOpportunityUpdate(InputSchema):
    status: ReturnOpportunityStatus
    contact_channel: ContactChannel | None = None


class ReturnOpportunityOut(OutputSchema):
    id: UUID
    patient_id: UUID
    procedure_id: UUID
    due_date: date
    potential_value: MoneyOut
    status: ReturnOpportunityStatus
    contacted_at: datetime | None
    contact_channel: ContactChannel | None
    resolved_by_sale_id: UUID | None
    dismissed_at: datetime | None
