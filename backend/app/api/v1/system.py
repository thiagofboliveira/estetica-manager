from fastapi import APIRouter, HTTPException, status

from app.api.deps import SystemSvc
from app.schemas.system import SystemSetupInput, SystemStatusOutput
from app.schemas.user import UserOutput

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusOutput)
def get_system_status(service: SystemSvc) -> SystemStatusOutput:
    """Verifica se o sistema possui usuários cadastrados ou necessita de setup inicial."""
    status_data = service.get_status()
    return SystemStatusOutput(**status_data)


@router.post("/setup", response_model=UserOutput, status_code=status.HTTP_201_CREATED)
def setup_system(body: SystemSetupInput, service: SystemSvc) -> UserOutput:
    """Cria o Super Administrador e o tenant inicial no primeiro acesso.
    
    Falha com 400 se o sistema já possuir usuários cadastrados.
    """
    try:
        user = service.setup_root(
            clinic_name=body.clinic_name,
            admin_name=body.admin_name,
            email=body.email,
            password=body.password,
        )
        return UserOutput.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
