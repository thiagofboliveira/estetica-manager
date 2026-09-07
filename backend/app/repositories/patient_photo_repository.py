from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.patient_photo import PatientPhoto, PhotoType
from app.repositories.base import TenantRepository


class PatientPhotoRepository(TenantRepository[PatientPhoto]):
    model = PatientPhoto

    def list_by_patient(
        self,
        patient_id: UUID,
        procedure_id: UUID | None = None,
        photo_type: PhotoType | None = None,
    ) -> list[PatientPhoto]:
        stmt = (
            self._scoped()
            .options(joinedload(PatientPhoto.procedure))
            .where(
                PatientPhoto.patient_id == patient_id,
                PatientPhoto.is_active.is_(True),
            )
        )
        if procedure_id is not None:
            stmt = stmt.where(PatientPhoto.procedure_id == procedure_id)
        if photo_type is not None:
            stmt = stmt.where(PatientPhoto.photo_type == photo_type)

        stmt = stmt.order_by(
            PatientPhoto.captured_at.desc(), PatientPhoto.created_at.desc()
        )
        return list(self._session.scalars(stmt).unique())

    def get_with_procedure(self, photo_id: UUID) -> PatientPhoto | None:
        stmt = (
            self._scoped()
            .options(joinedload(PatientPhoto.procedure))
            .where(
                PatientPhoto.id == photo_id,
                PatientPhoto.is_active.is_(True),
            )
        )
        return self._session.scalars(stmt).unique().one_or_none()
