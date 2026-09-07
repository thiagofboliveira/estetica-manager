"""Endpoints autenticados para Gestão da Anamnese (AN-05)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AnamnesisSvc
from app.schemas.anamnesis import (
    AnamnesisQuestionCreate,
    AnamnesisQuestionOut,
    AnamnesisQuestionUpdate,
    AnamnesisReorderQuestionsInput,
    AnamnesisSubmissionOut,
    AnamnesisTemplateOut,
    AnamnesisTemplateUpdate,
)
from app.services.anamnesis_service import (
    AnamnesisNotFoundError,
    AnamnesisQuestionNotFoundError,
)

router = APIRouter(prefix="/anamnesis", tags=["anamnesis"])


@router.get("/template", response_model=AnamnesisTemplateOut)
def get_template(svc: AnamnesisSvc) -> AnamnesisTemplateOut:
    """Retorna o template ativo com todas as perguntas estruturadas."""
    template = svc.get_or_create_default_template()
    return AnamnesisTemplateOut.model_validate(template)


@router.put("/template", response_model=AnamnesisTemplateOut)
def update_template(
    payload: AnamnesisTemplateUpdate, svc: AnamnesisSvc
) -> AnamnesisTemplateOut:
    """Atualiza configurações do template de anamnese."""
    template = svc.get_or_create_default_template()
    try:
        updated = svc.update_template(template.id, payload)
        return AnamnesisTemplateOut.model_validate(updated)
    except AnamnesisNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post(
    "/questions",
    response_model=AnamnesisQuestionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    payload: AnamnesisQuestionCreate, svc: AnamnesisSvc
) -> AnamnesisQuestionOut:
    """Adiciona uma nova pergunta ao template ativo."""
    template = svc.get_or_create_default_template()
    try:
        q = svc.create_question(template.id, payload)
        return AnamnesisQuestionOut.model_validate(q)
    except AnamnesisNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.put("/questions/{question_id}", response_model=AnamnesisQuestionOut)
def update_question(
    question_id: UUID, payload: AnamnesisQuestionUpdate, svc: AnamnesisSvc
) -> AnamnesisQuestionOut:
    """Atualiza uma pergunta existente."""
    try:
        q = svc.update_question(question_id, payload)
        return AnamnesisQuestionOut.model_validate(q)
    except AnamnesisQuestionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: UUID, svc: AnamnesisSvc) -> None:
    """Remove uma pergunta do template."""
    try:
        svc.delete_question(question_id)
    except AnamnesisQuestionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/questions/reorder", response_model=list[AnamnesisQuestionOut])
def reorder_questions(
    payload: AnamnesisReorderQuestionsInput, svc: AnamnesisSvc
) -> list[AnamnesisQuestionOut]:
    """Reordena as perguntas do formulário."""
    template = svc.get_or_create_default_template()
    try:
        questions = svc.reorder_questions(template.id, payload)
        return [AnamnesisQuestionOut.model_validate(q) for q in questions]
    except AnamnesisNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/submissions", response_model=list[AnamnesisSubmissionOut])
def list_submissions(
    svc: AnamnesisSvc,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[AnamnesisSubmissionOut]:
    """Lista as fichas de anamnese preenchidas recentemente."""
    subs = svc.list_submissions(limit=limit, offset=offset)
    return [AnamnesisSubmissionOut.model_validate(s) for s in subs]


@router.get(
    "/patient/{patient_id}", response_model=list[AnamnesisSubmissionOut]
)
def get_patient_submissions(
    patient_id: UUID, svc: AnamnesisSvc
) -> list[AnamnesisSubmissionOut]:
    """Retorna histórico de anamnese de um paciente específico."""
    subs = svc.get_patient_submissions(patient_id)
    return [AnamnesisSubmissionOut.model_validate(s) for s in subs]


@router.post("/submissions/token", response_model=AnamnesisSubmissionOut)
def generate_submission_token(
    svc: AnamnesisSvc,
    booking_id: UUID | None = None,
    patient_id: UUID | None = None,
    patient_name: str = "Paciente",
    patient_phone: str | None = None,
) -> AnamnesisSubmissionOut:
    """Gera um link/token de preenchimento para um paciente ou agendamento."""
    template = svc.get_or_create_default_template()
    sub = svc.create_or_get_submission(
        template_id=template.id,
        patient_id=patient_id,
        booking_id=booking_id,
        patient_name=patient_name,
        patient_phone=patient_phone,
    )
    return AnamnesisSubmissionOut.model_validate(sub)
