from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import PatientSvc
from app.schemas.patient import (
    PatientBatchImportRequest,
    PatientBatchImportResult,
    PatientCreate,
    PatientOut,
    PatientUpdate,
)
from app.services.patient_service import PatientNotFoundError

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, svc: PatientSvc) -> PatientOut:
    return PatientOut.model_validate(svc.create(payload))


@router.post("/import", response_model=PatientBatchImportResult)
def import_patients(
    payload: PatientBatchImportRequest, svc: PatientSvc
) -> PatientBatchImportResult:
    """Importa pacientes em lote com deduplicação por telefone (EPIC-S2-03, TASK-BACK-S2-15)."""
    return svc.batch_import(payload)


@router.get("", response_model=list[PatientOut])
def list_patients(
    svc: PatientSvc,
    search: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[PatientOut]:
    patients = svc.list(limit=limit, offset=offset, search=search)
    return [PatientOut.model_validate(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: UUID, svc: PatientSvc) -> PatientOut:
    try:
        patient = svc.get(patient_id)
    except PatientNotFoundError as exc:
        # 404, nunca 403: "existe mas não é seu" já vaza a existência
        # do recurso de outro tenant.
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc
    return PatientOut.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: UUID, payload: PatientUpdate, svc: PatientSvc
) -> PatientOut:
    try:
        patient = svc.update(patient_id, payload)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc
    return PatientOut.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_patient(patient_id: UUID, svc: PatientSvc) -> None:
    """Arquiva (is_active=False). Nunca hard delete — ver MVP v6 §10."""
    try:
        svc.archive(patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc


@router.post("/{patient_id}/anonymize", response_model=PatientOut)
def anonymize_patient(patient_id: UUID, svc: PatientSvc) -> PatientOut:
    """Anonimiza os dados pessoais do paciente atendendo à LGPD (TASK-061)."""
    try:
        patient = svc.anonymize(patient_id)
        return PatientOut.model_validate(patient)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc


@router.post("/{patient_id}/opt-out", response_model=PatientOut)
def opt_out_patient(patient_id: UUID, svc: PatientSvc) -> PatientOut:
    """Registra opt-out de mensagens de WhatsApp para o paciente (TASK-060)."""
    try:
        patient = svc.opt_out(patient_id)
        return PatientOut.model_validate(patient)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc


@router.get("/{patient_id}/export")
def export_patient_data(patient_id: UUID, svc: PatientSvc) -> dict:
    """Exporta os dados do titular em formato legível e interoperável para portabilidade (LGPD Art. 18, V, TASK-062)."""
    try:
        return svc.export_data(patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrada"
        ) from exc
