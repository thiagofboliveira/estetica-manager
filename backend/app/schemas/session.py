from datetime import datetime
from uuid import UUID

from app.domain.sales.session_state_machine import SessionStatus
from app.models.procedure import Modality
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class SessionUpdate(InputSchema):
    scheduled_at: datetime | None = None
    status: SessionStatus | None = None
    cost_override: str | None = None
    notes: str | None = None


class SessionDetailOut(OutputSchema):
    id: UUID
    sale_item_id: UUID
    sequence_number: int
    scheduled_at: datetime | None
    completed_at: datetime | None
    confirmed_at: datetime | None = None
    status: SessionStatus
    modality: Modality
    cost_override: MoneyOut | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AgendaItemOut(OutputSchema):
    id: UUID
    type: str = "SESSION"  # "SESSION" | "BOOKING"
    patient_id: UUID | None
    patient_name: str
    patient_phone: str | None = None
    procedure_name: str
    scheduled_at: datetime
    modality: Modality
    status: str
    sequence_number: int | None = None
    total_sessions: int | None = None
    note: str | None = None
    confirmed_at: datetime | None = None


class UnconfirmedSessionOut(OutputSchema):
    session_id: UUID
    type: str = "SESSION"  # "SESSION" | "BOOKING"
    patient_name: str
    patient_phone: str | None
    procedure_name: str
    scheduled_at: datetime
    modality: Modality
    whatsapp_link: str | None
    consent_whatsapp: bool
    confirmed_at: datetime | None = None


class OpenPackageOut(OutputSchema):
    sale_id: UUID
    sale_item_id: UUID
    patient_id: UUID
    patient_name: str
    patient_phone: str | None = None
    procedure_id: UUID
    procedure_name: str
    total_sessions: int
    used_sessions: int
    pending_sessions: int
    last_session_completed_at: datetime | None
    next_pending_session_id: UUID | None
