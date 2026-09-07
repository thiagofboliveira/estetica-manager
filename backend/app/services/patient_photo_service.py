from datetime import UTC, datetime
from uuid import UUID

from app.models.patient_photo import PatientPhoto, PhotoType
from app.repositories.patient import PatientRepository
from app.repositories.patient_photo_repository import PatientPhotoRepository
from app.repositories.procedure import ProcedureRepository
from app.schemas.patient_photo import PatientPhotoCreate, PatientPhotoUpdate
from app.services.patient_service import PatientNotFoundError


class PhotoNotFoundError(Exception):
    pass


class ProcedureNotFoundError(Exception):
    pass


class PatientPhotoService:
    def __init__(
        self,
        repo: PatientPhotoRepository,
        patient_repo: PatientRepository,
        procedure_repo: ProcedureRepository | None = None,
    ) -> None:
        self._repo = repo
        self._patient_repo = patient_repo
        self._procedure_repo = procedure_repo

    def create(self, patient_id: UUID, dto: PatientPhotoCreate) -> PatientPhoto:
        patient = self._patient_repo.get(patient_id)
        if not patient or not patient.is_active:
            raise PatientNotFoundError(f"Paciente {patient_id} não encontrada")

        if dto.procedure_id and self._procedure_repo:
            procedure = self._procedure_repo.get(dto.procedure_id)
            if not procedure:
                raise ProcedureNotFoundError(
                    f"Procedimento {dto.procedure_id} não encontrado"
                )

        photo = PatientPhoto(
            patient_id=patient_id,
            procedure_id=dto.procedure_id,
            photo_type=dto.photo_type,
            image_url=dto.image_url,
            caption=dto.caption,
            captured_at=dto.captured_at or datetime.now(UTC),
            authorized_social_media=dto.authorized_social_media,
        )
        saved = self._repo.add(photo)
        return saved

    def list_by_patient(
        self,
        patient_id: UUID,
        procedure_id: UUID | None = None,
        photo_type: PhotoType | None = None,
    ) -> list[PatientPhoto]:
        patient = self._patient_repo.get(patient_id)
        if not patient or not patient.is_active:
            raise PatientNotFoundError(f"Paciente {patient_id} não encontrada")

        return self._repo.list_by_patient(
            patient_id=patient_id,
            procedure_id=procedure_id,
            photo_type=photo_type,
        )

    def get(self, photo_id: UUID) -> PatientPhoto:
        photo = self._repo.get_with_procedure(photo_id)
        if not photo or not photo.is_active:
            raise PhotoNotFoundError(f"Foto {photo_id} não encontrada")
        return photo

    def update(self, photo_id: UUID, dto: PatientPhotoUpdate) -> PatientPhoto:
        photo = self.get(photo_id)
        if dto.procedure_id is not None and self._procedure_repo:
            if dto.procedure_id:
                procedure = self._procedure_repo.get(dto.procedure_id)
                if not procedure:
                    raise ProcedureNotFoundError(
                        f"Procedimento {dto.procedure_id} não encontrado"
                    )
            photo.procedure_id = dto.procedure_id

        if dto.photo_type is not None:
            photo.photo_type = dto.photo_type
        if dto.caption is not None:
            photo.caption = dto.caption
        if dto.captured_at is not None:
            photo.captured_at = dto.captured_at
        if dto.authorized_social_media is not None:
            photo.authorized_social_media = dto.authorized_social_media

        return photo

    def delete(self, photo_id: UUID) -> None:
        photo = self.get(photo_id)
        photo.is_active = False
