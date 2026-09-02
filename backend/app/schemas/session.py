from datetime import datetime
from uuid import UUID

from app.domain.sales.session_state_machine import SessionStatus
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class SessionUpdate(InputSchema):
    status: SessionStatus


class SessionDetailOut(OutputSchema):
    id: UUID
    sale_item_id: UUID
    sequence_number: int
    scheduled_at: datetime | None
    completed_at: datetime | None
    status: SessionStatus
    modality: str
    cost_override: MoneyOut | None
    notes: str | None
