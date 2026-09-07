from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import PatientPhotoSvc
from app.models.patient_photo import PhotoType
from app.schemas.patient_photo import (
    PatientPhotoCreate,
    PatientPhotoOut,
    PatientPhotoUpdate,
)
from app.services.patient_photo_service import (
    PhotoNotFoundError,
    ProcedureNotFoundError,
)
from app.services.patient_service import PatientNotFoundError

router = APIRouter(prefix="/patients/{patient_id}/photos", tags=["patient_photos"])


def _to_out(photo) -> PatientPhotoOut:
    return PatientPhotoOut(
        id=photo.id,
        patient_id=photo.patient_id,
        procedure_id=photo.procedure_id,
        procedure_name=photo.procedure.name if photo.procedure else None,
        photo_type=photo.photo_type,
        image_url=photo.image_url,
        caption=photo.caption,
        captured_at=photo.captured_at,
        authorized_social_media=photo.authorized_social_media,
        created_at=photo.created_at,
    )


@router.get("", response_model=list[PatientPhotoOut])
def list_photos(
    patient_id: UUID,
    svc: PatientPhotoSvc,
    procedure_id: UUID | None = Query(default=None),
    photo_type: PhotoType | None = Query(default=None),
) -> list[PatientPhotoOut]:
    try:
        photos = svc.list_by_patient(
            patient_id=patient_id,
            procedure_id=procedure_id,
            photo_type=photo_type,
        )
        return [_to_out(p) for p in photos]
    except PatientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrada",
        ) from exc


@router.post("", response_model=PatientPhotoOut, status_code=status.HTTP_201_CREATED)
def create_photo(
    patient_id: UUID,
    payload: PatientPhotoCreate,
    svc: PatientPhotoSvc,
) -> PatientPhotoOut:
    try:
        photo = svc.create(patient_id=patient_id, dto=payload)
        return _to_out(photo)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrada",
        ) from exc
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Procedimento não encontrado",
        ) from exc


@router.get("/{photo_id}", response_model=PatientPhotoOut)
def get_photo(
    patient_id: UUID,
    photo_id: UUID,
    svc: PatientPhotoSvc,
) -> PatientPhotoOut:
    try:
        photo = svc.get(photo_id)
        if photo.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foto não encontrada para esta paciente",
            )
        return _to_out(photo)
    except PhotoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto não encontrada",
        ) from exc


@router.patch("/{photo_id}", response_model=PatientPhotoOut)
def update_photo(
    patient_id: UUID,
    photo_id: UUID,
    payload: PatientPhotoUpdate,
    svc: PatientPhotoSvc,
) -> PatientPhotoOut:
    try:
        photo = svc.get(photo_id)
        if photo.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foto não encontrada para esta paciente",
            )
        updated = svc.update(photo_id, payload)
        return _to_out(updated)
    except PhotoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto não encontrada",
        ) from exc
    except ProcedureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Procedimento não encontrado",
        ) from exc


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    patient_id: UUID,
    photo_id: UUID,
    svc: PatientPhotoSvc,
) -> None:
    try:
        photo = svc.get(photo_id)
        if photo.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foto não encontrada para esta paciente",
            )
        svc.delete(photo_id)
    except PhotoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto não encontrada",
        ) from exc
