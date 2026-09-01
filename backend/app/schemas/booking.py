from datetime import datetime
from uuid import UUID

from app.domain.bookings.enums import BookingStatus
from app.models.procedure import Modality
from app.schemas.base import InputSchema, OutputSchema


class BookingCreate(InputSchema):
    patient_id: UUID | None = None
    patient_name_hint: str | None = None
    scheduled_at: datetime
    modality: Modality = Modality.IN_PERSON
    note: str | None = None


class BookingUpdate(InputSchema):
    patient_id: UUID | None = None
    patient_name_hint: str | None = None
    scheduled_at: datetime | None = None
    modality: Modality | None = None
    note: str | None = None
    status: BookingStatus | None = None


class BookingOut(OutputSchema):
    id: UUID
    patient_id: UUID | None
    patient_name: str | None = None
    patient_name_hint: str | None = None
    scheduled_at: datetime
    modality: Modality
    note: str | None
    status: BookingStatus
    sale_id: UUID | None
    created_at: datetime
    updated_at: datetime
