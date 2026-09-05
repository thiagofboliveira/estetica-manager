from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.bookings.enums import BookingStatus
from app.models.procedure import Modality
from app.schemas.base import InputSchema, OutputSchema


class BookingCreate(InputSchema):
    patient_id: UUID | None = None
    patient_name_hint: str | None = None
    patient_phone: str | None = None
    procedure_id: UUID | None = None
    scheduled_at: datetime
    modality: Modality = Modality.IN_PERSON
    note: str | None = None


class BookingUpdate(InputSchema):
    patient_id: UUID | None = None
    patient_name_hint: str | None = None
    patient_phone: str | None = None
    procedure_id: UUID | None = None
    scheduled_at: datetime | None = None
    modality: Modality | None = None
    note: str | None = None
    status: BookingStatus | None = None


class BookingOut(OutputSchema):
    id: UUID
    patient_id: UUID | None
    patient_name: str | None = None
    patient_name_hint: str | None = None
    patient_phone: str | None = None
    procedure_id: UUID | None = None
    procedure_name: str | None = None
    scheduled_at: datetime
    modality: Modality
    note: str | None
    status: BookingStatus
    management_token: str
    sale_id: UUID | None
    created_at: datetime
    updated_at: datetime


class PublicBookingCreate(InputSchema):
    procedure_id: UUID
    scheduled_at: datetime
    patient_name: str
    patient_phone: str
    note: str | None = None


class PublicBookingReschedule(InputSchema):
    scheduled_at: datetime | None = None
    procedure_id: UUID | None = None
    note: str | None = None


class PublicProcedureOut(OutputSchema):
    id: UUID
    name: str
    price: Decimal
    return_interval_days: int | None = None
    session_plan: str
    image_url: str | None = None


class PublicProfessionalInfo(OutputSchema):
    name: str
    slug: str
    bio: str | None = None
    avatar_url: str | None = None
    specialty: str | None = None
    procedures: list[PublicProcedureOut]


class PublicBookingOut(OutputSchema):
    id: UUID
    professional_name: str
    professional_slug: str | None = None
    patient_name: str
    patient_phone: str | None = None
    procedure_id: UUID | None = None
    procedure_name: str | None = None
    procedure_price: Decimal | None = None
    scheduled_at: datetime
    status: BookingStatus
    note: str | None = None
    management_token: str
