from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentProfessional, CurrentUser, DbSession, UserSvc
from app.models.professional import Professional
from app.repositories.professional import ProfessionalRepository
from app.schemas.user import (
    PublicProfileUpdate,
    TermsAcceptInput,
    UserCreateInput,
    UserOutput,
    UserUpdateInput,
)
from app.services.user_service import UserServiceError

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOutput)
def get_current_user_profile(
    user: CurrentUser, session: DbSession, professional_id: CurrentProfessional
) -> UserOutput:
    """Retorna os dados do usuário autenticado na sessão atual, incluindo slug da agenda pública."""
    out = UserOutput.model_validate(user)
    prof = ProfessionalRepository(session, professional_id).get_by_id(professional_id)
    if prof:
        if not prof.slug:
            from uuid import uuid4

            from app.core.slug import generate_slug

            candidate_slug = generate_slug(prof.name, prof.id)
            stmt = select(Professional).where(
                Professional.slug == candidate_slug, Professional.id != professional_id
            )
            if session.scalars(stmt).first():
                candidate_slug = f"{candidate_slug}-{uuid4().hex[:4]}"
            prof.slug = candidate_slug
            session.flush()

        out.slug = prof.slug
        out.bio = prof.bio
        out.avatar_url = prof.avatar_url
        out.specialty = prof.specialty
    return out


@router.patch("/me/public-profile", response_model=UserOutput)
def update_public_profile(
    body: PublicProfileUpdate,
    user: CurrentUser,
    session: DbSession,
    professional_id: CurrentProfessional,
) -> UserOutput:
    """Atualiza o link público (slug), bio, foto/logo e especialidade da profissional."""
    prof_repo = ProfessionalRepository(session, professional_id)
    prof = prof_repo.get_by_id(professional_id)
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de profissional não encontrado",
        )

    if body.slug is not None:
        clean_slug = body.slug.strip().lower()
        # Valida se slug já está em uso por outro profissional
        stmt = select(Professional).where(
            Professional.slug == clean_slug, Professional.id != professional_id
        )
        existing = session.scalars(stmt).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este link de agendamento já está em uso. Por favor escolha outro.",
            )
        prof.slug = clean_slug

    if body.bio is not None:
        prof.bio = body.bio.strip()

    if body.avatar_url is not None:
        prof.avatar_url = body.avatar_url.strip() or None

    if body.specialty is not None:
        prof.specialty = body.specialty.strip() or None

    session.flush()

    out = UserOutput.model_validate(user)
    out.slug = prof.slug
    out.bio = prof.bio
    out.avatar_url = prof.avatar_url
    out.specialty = prof.specialty
    return out


@router.post("/me/accept-terms", response_model=UserOutput)
def accept_terms(
    body: TermsAcceptInput,
    user: CurrentUser,
    service: UserSvc,
    request: Request,
) -> UserOutput:
    """Registra formalmente o aceite dos Termos de Uso e DPA/LGPD pelo usuário (G-10)."""
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    updated_user = service.accept_terms(
        user_id=user.id,
        terms_version=body.terms_version,
        ip_address=ip,
        user_agent=user_agent,
    )
    return UserOutput.model_validate(updated_user)


@router.get("", response_model=list[UserOutput])
def list_users(admin: AdminUser, service: UserSvc) -> list[UserOutput]:
    """Lista os usuários da clínica do administrador. Exige permissão de administrador."""
    users = service.list_users(clinic_id=admin.clinic_id)
    return [UserOutput.model_validate(u) for u in users]


@router.post("", response_model=UserOutput, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateInput,
    admin: AdminUser,
    service: UserSvc,
) -> UserOutput:
    """Cria um novo usuário na clínica do administrador. Exige permissão de administrador."""
    target_clinic_id = (
        admin.clinic_id if admin.clinic_id is not None else body.clinic_id
    )
    try:
        user = service.create_user(
            name=body.name,
            email=body.email,
            role=body.role,
            is_superuser=body.is_superuser if admin.is_superuser else False,
            clinic_id=target_clinic_id,
        )
        return UserOutput.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.put("/{user_id}", response_model=UserOutput)
def update_user(
    user_id: UUID,
    body: UserUpdateInput,
    admin: AdminUser,
    service: UserSvc,
) -> UserOutput:
    """Atualiza dados, papel ou status de um usuário. Exige permissão de administrador."""
    try:
        target = service.get_user(user_id)
        if admin.clinic_id is not None and target.clinic_id != admin.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado na clínica",
            )

        user = service.update_user(
            user_id=user_id,
            current_user_id=admin.id,
            name=body.name,
            role=body.role,
            is_active=body.is_active,
            is_superuser=body.is_superuser if admin.is_superuser else None,
            clinic_id=body.clinic_id if admin.is_superuser else None,
        )
        return UserOutput.model_validate(user)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{user_id}", response_model=UserOutput)
def deactivate_user(
    user_id: UUID,
    admin: AdminUser,
    service: UserSvc,
) -> UserOutput:
    """Inativa o acesso de um usuário. Não permite inativar a própria conta autenticada."""
    try:
        target = service.get_user(user_id)
        if admin.clinic_id is not None and target.clinic_id != admin.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado na clínica",
            )

        user = service.deactivate_user(
            user_id=user_id,
            current_user_id=admin.id,
        )
        return UserOutput.model_validate(user)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
