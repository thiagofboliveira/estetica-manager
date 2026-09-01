from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import GlobalSuperAdminUser, SystemClinicSvc, SystemUserSvc
from app.schemas.clinic import ClinicCreateInput, ClinicOutput, ClinicUpdateInput
from app.schemas.user import UserCreateInput, UserOutput, UserUpdateInput

router = APIRouter(prefix="/super-admin", tags=["super-admin"])


# ==============================================================================
# Endpoints de Plataforma — Clínicas ([BACK-08])
# ==============================================================================


@router.get("/clinics", response_model=list[ClinicOutput])
def list_all_clinics(
    _superadmin: GlobalSuperAdminUser,
    service: SystemClinicSvc,
) -> list[ClinicOutput]:
    """Lista todas as clínicas cadastradas na plataforma SaaS com total de usuários."""
    clinics_data = service.list_clinics()
    return [ClinicOutput(**c) for c in clinics_data]


@router.post(
    "/clinics", response_model=ClinicOutput, status_code=status.HTTP_201_CREATED
)
def create_clinic(
    body: ClinicCreateInput,
    _superadmin: GlobalSuperAdminUser,
    service: SystemClinicSvc,
) -> ClinicOutput:
    """Cria uma nova clínica (tenant) na plataforma SaaS."""
    clinic = service.create_clinic(
        name=body.name,
        document=body.document,
        phone=body.phone,
        email=body.email,
        plan=body.plan,
    )
    return ClinicOutput(
        id=clinic.id,
        name=clinic.name,
        document=clinic.document,
        phone=clinic.phone,
        email=clinic.email,
        plan=clinic.plan,
        is_active=clinic.is_active,
        users_count=0,
        created_at=clinic.created_at,
        updated_at=clinic.updated_at,
    )


@router.get("/clinics/{clinic_id}", response_model=ClinicOutput)
def get_clinic_detail(
    clinic_id: UUID,
    _superadmin: GlobalSuperAdminUser,
    service: SystemClinicSvc,
) -> ClinicOutput:
    """Retorna os detalhes de uma clínica."""
    try:
        clinic = service.get_clinic(clinic_id)
        users_count = service._clinic_repo.count_users(clinic.id)
        return ClinicOutput(
            id=clinic.id,
            name=clinic.name,
            document=clinic.document,
            phone=clinic.phone,
            email=clinic.email,
            plan=clinic.plan,
            is_active=clinic.is_active,
            users_count=users_count,
            created_at=clinic.created_at,
            updated_at=clinic.updated_at,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put("/clinics/{clinic_id}", response_model=ClinicOutput)
def update_clinic(
    clinic_id: UUID,
    body: ClinicUpdateInput,
    _superadmin: GlobalSuperAdminUser,
    service: SystemClinicSvc,
) -> ClinicOutput:
    """Atualiza dados, plano ou status de uma clínica."""
    try:
        clinic = service.update_clinic(
            clinic_id=clinic_id,
            name=body.name,
            document=body.document,
            phone=body.phone,
            email=body.email,
            plan=body.plan,
            is_active=body.is_active,
        )
        users_count = service._clinic_repo.count_users(clinic.id)
        return ClinicOutput(
            id=clinic.id,
            name=clinic.name,
            document=clinic.document,
            phone=clinic.phone,
            email=clinic.email,
            plan=clinic.plan,
            is_active=clinic.is_active,
            users_count=users_count,
            created_at=clinic.created_at,
            updated_at=clinic.updated_at,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/clinics/{clinic_id}", response_model=ClinicOutput)
def deactivate_clinic(
    clinic_id: UUID,
    _superadmin: GlobalSuperAdminUser,
    service: SystemClinicSvc,
) -> ClinicOutput:
    """Inativa uma clínica na plataforma."""
    try:
        clinic = service.deactivate_clinic(clinic_id)
        users_count = service._clinic_repo.count_users(clinic.id)
        return ClinicOutput(
            id=clinic.id,
            name=clinic.name,
            document=clinic.document,
            phone=clinic.phone,
            email=clinic.email,
            plan=clinic.plan,
            is_active=clinic.is_active,
            users_count=users_count,
            created_at=clinic.created_at,
            updated_at=clinic.updated_at,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ==============================================================================
# Endpoints de Plataforma — Usuários Globais ([BACK-09])
# ==============================================================================


@router.get("/users", response_model=list[UserOutput])
def list_global_users(
    _superadmin: GlobalSuperAdminUser,
    user_service: SystemUserSvc,
    clinic_service: SystemClinicSvc,
) -> list[UserOutput]:
    """Lista todos os usuários da plataforma com mapeamento do nome da clínica."""
    users = user_service.list_users()
    clinics_map = {c["id"]: c["name"] for c in clinic_service.list_clinics()}

    result = []
    for u in users:
        c_name = clinics_map.get(u.clinic_id) if u.clinic_id else None
        result.append(
            UserOutput(
                id=u.id,
                clinic_id=u.clinic_id,
                clinic_name=c_name,
                name=u.name,
                email=u.email,
                role=u.role,
                is_superuser=u.is_superuser,
                is_active=u.is_active,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
        )
    return result


@router.post(
    "/users", response_model=UserOutput, status_code=status.HTTP_201_CREATED
)
def create_global_user(
    body: UserCreateInput,
    _superadmin: GlobalSuperAdminUser,
    user_service: SystemUserSvc,
) -> UserOutput:
    """Cria um novo usuário na plataforma vinculando-o à clínica informada."""
    try:
        user = user_service.create_user(
            name=body.name,
            email=body.email,
            role=body.role,
            is_superuser=body.is_superuser,
            clinic_id=body.clinic_id,
        )
        return UserOutput.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put("/users/{user_id}", response_model=UserOutput)
def update_global_user(
    user_id: UUID,
    body: UserUpdateInput,
    superadmin: GlobalSuperAdminUser,
    user_service: SystemUserSvc,
) -> UserOutput:
    """Atualiza dados, papel ou transfere a clínica de qualquer usuário."""
    try:
        user = user_service.update_user(
            user_id=user_id,
            current_user_id=superadmin.id,
            name=body.name,
            email=body.email,
            role=body.role,
            is_active=body.is_active,
            is_superuser=body.is_superuser,
            clinic_id=body.clinic_id,
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
