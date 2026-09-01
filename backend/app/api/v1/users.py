from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, CurrentUser, UserSvc
from app.schemas.user import UserCreateInput, UserOutput, UserUpdateInput

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOutput)
def get_current_user_profile(user: CurrentUser) -> UserOutput:
    """Retorna os dados do usuário autenticado na sessão atual."""
    return UserOutput.model_validate(user)


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
    target_clinic_id = admin.clinic_id if admin.clinic_id is not None else body.clinic_id
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
