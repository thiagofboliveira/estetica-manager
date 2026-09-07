from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.patient_photo import PhotoType
from app.schemas.base import InputSchema, OutputSchema


class PatientPhotoCreate(InputSchema):
    photo_type: PhotoType = PhotoType.BEFORE
    procedure_id: UUID | None = None
    image_url: str = Field(min_length=1, description="Data URI base64 ou URL da imagem")
    caption: str | None = Field(default=None, max_length=255)
    captured_at: datetime | None = None
    authorized_social_media: bool = False


class PatientPhotoUpdate(InputSchema):
    photo_type: PhotoType | None = None
    procedure_id: UUID | None = None
    caption: str | None = Field(default=None, max_length=255)
    captured_at: datetime | None = None
    authorized_social_media: bool | None = None


class PatientPhotoOut(OutputSchema):
    id: UUID
    patient_id: UUID
    procedure_id: UUID | None = None
    procedure_name: str | None = None
    photo_type: PhotoType
    image_url: str
    caption: str | None = None
    captured_at: datetime
    authorized_social_media: bool
    created_at: datetime
