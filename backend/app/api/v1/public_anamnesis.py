"""Endpoints públicos para preenchimento de Anamnese pelo paciente (AN-06)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.public_agenda import (
    PublicBookingRateLimit,
    PublicQueryRateLimit,
)
from app.db.session import tenant_session, unsafe_session_without_tenant
from app.models.anamnesis import (
    AnamnesisSubmission,
)
from app.models.booking import Booking
from app.repositories.anamnesis import (
    AnamnesisQuestionRepository,
    AnamnesisSubmissionRepository,
    AnamnesisTemplateRepository,
)
from app.repositories.clinic import ClinicRepository
from app.repositories.professional import ProfessionalRepository
from app.schemas.anamnesis import (
    AnamnesisQuestionOut,
    AnamnesisSubmissionOut,
    PublicAnamnesisFormOut,
    PublicAnamnesisSubmitInput,
)
from app.services.anamnesis_service import AnamnesisService

router = APIRouter(prefix="/public/anamnesis", tags=["public-anamnesis"])


def _resolve_submission_tenant(token: str) -> tuple[UUID, UUID]:
    """Descobre submission_id e professional_id a partir do token público."""
    clean_token = token.strip()
    with unsafe_session_without_tenant("lookup anamnesis submission tenant") as sys_sess:
        stmt = select(
            AnamnesisSubmission.id, AnamnesisSubmission.professional_id
        ).where(AnamnesisSubmission.public_token == clean_token)
        row = sys_sess.execute(stmt).first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ficha de anamnese não encontrada ou link inválido.",
            )
        return row[0], row[1]


def _build_anamnesis_service(session, professional_id: UUID) -> AnamnesisService:
    return AnamnesisService(
        template_repo=AnamnesisTemplateRepository(session, professional_id),
        question_repo=AnamnesisQuestionRepository(session, professional_id),
        submission_repo=AnamnesisSubmissionRepository(session, professional_id),
    )


@router.get("/by-booking/{booking_id}", response_model=AnamnesisSubmissionOut)
def get_or_create_booking_anamnesis(
    booking_id: UUID,
    token: str = Query(..., min_length=10),
    _rate_limit: PublicQueryRateLimit = None,
) -> AnamnesisSubmissionOut:
    """Obtém ou gera ficha de anamnese vinculada a um agendamento público."""
    with unsafe_session_without_tenant("lookup booking tenant for anamnesis") as sys_sess:
        stmt = select(
            Booking.id,
            Booking.professional_id,
            Booking.patient_name_hint,
            Booking.patient_phone,
            Booking.patient_id,
        ).where(
            Booking.id == booking_id,
            Booking.management_token == token.strip(),
        )
        row = sys_sess.execute(stmt).first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado ou link inválido.",
            )
        _, prof_id, p_name, p_phone, pat_id = row

    with tenant_session(prof_id) as session:
        svc = _build_anamnesis_service(session, prof_id)
        template = svc.get_or_create_default_template()

        sub = svc.create_or_get_submission(
            template_id=template.id,
            patient_id=pat_id,
            booking_id=booking_id,
            patient_name=p_name or "Paciente",
            patient_phone=p_phone,
        )
        return AnamnesisSubmissionOut.model_validate(sub)


@router.get("/{token}", response_model=PublicAnamnesisFormOut)
def get_public_anamnesis_form(
    token: str,
    _rate_limit: PublicQueryRateLimit = None,
) -> PublicAnamnesisFormOut:
    """Retorna o formulário público com dados da clínica e perguntas ativas."""
    sub_id, prof_id = _resolve_submission_tenant(token)

    with tenant_session(prof_id) as session:
        svc = _build_anamnesis_service(session, prof_id)
        sub = svc.submission_repo.get(sub_id)
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ficha de anamnese não encontrada.",
            )

        template = svc.template_repo.get_by_id(sub.template_id)
        if not template:
            template = svc.get_or_create_default_template()

        questions = svc.question_repo.list_by_template(template.id, active_only=True)
        prof = ProfessionalRepository(session, prof_id).get_by_id(prof_id)

        clinic_name = None
        if prof and prof.clinic_id:
            clinic = ClinicRepository(session).get_by_id(prof.clinic_id)
            clinic_name = clinic.name if clinic else None

        return PublicAnamnesisFormOut(
            token=sub.public_token,
            clinic_name=clinic_name,
            professional_name=prof.name if prof else "Profissional",
            professional_slug=prof.slug if prof else None,
            template_title=template.title,
            template_description=template.description,
            patient_name=sub.patient_name,
            patient_phone=sub.patient_phone,
            is_submitted=sub.submitted_at is not None,
            submitted_at=sub.submitted_at,
            questions=[AnamnesisQuestionOut.model_validate(q) for q in questions],
        )


@router.post("/{token}", response_model=AnamnesisSubmissionOut)
def submit_public_anamnesis(
    token: str,
    payload: PublicAnamnesisSubmitInput,
    _rate_limit: PublicBookingRateLimit = None,
) -> AnamnesisSubmissionOut:
    """Recebe e processa as respostas da anamnese preenchidas pelo paciente."""
    sub_id, prof_id = _resolve_submission_tenant(token)

    with tenant_session(prof_id) as session:
        svc = _build_anamnesis_service(session, prof_id)
        sub = svc.submission_repo.get(sub_id)
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ficha de anamnese não encontrada.",
            )

        template = svc.template_repo.get_by_id(sub.template_id)
        if not template:
            template = svc.get_or_create_default_template()

        questions = svc.question_repo.list_by_template(template.id, active_only=True)

        # Validação de campos obrigatórios
        for q in questions:
            if q.is_required:
                ans = payload.answers.get(str(q.id))
                if ans is None or (isinstance(ans, str) and not ans.strip()):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"A pergunta '{q.title}' é obrigatória.",
                    )

        updated_sub = svc.submit_answers(sub, payload, questions)
        return AnamnesisSubmissionOut.model_validate(updated_sub)
