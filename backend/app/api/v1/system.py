from fastapi import APIRouter, HTTPException, status

from app.api.deps import SystemSvc
from app.schemas.system import SystemSetupInput, SystemStatusOutput
from app.schemas.user import UserOutput
from app.services.system_service import SystemSetupError

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusOutput)
def get_system_status(service: SystemSvc) -> SystemStatusOutput:
    """Verifica se o sistema possui usuários cadastrados ou necessita de setup inicial."""
    status_data = service.get_status()
    return SystemStatusOutput(**status_data)


@router.post("/setup", response_model=UserOutput, status_code=status.HTTP_201_CREATED)
def setup_system(body: SystemSetupInput, service: SystemSvc) -> UserOutput:
    """Cria o Super Administrador e o tenant inicial no primeiro acesso.

    B-01: sem senha — o Supabase Auth manda um convite/magic-link para o
    e-mail informado; a pessoa define a senha ao clicar no link.
    Falha com 400 se o sistema já possuir usuários cadastrados, ou 502
    se o Supabase Auth recusar o convite (e-mail já existe lá, etc).
    """
    try:
        user = service.setup_root(
            clinic_name=body.clinic_name,
            admin_name=body.admin_name,
            email=body.email,
        )
        return UserOutput.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SystemSetupError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Não foi possível criar o usuário no Supabase Auth: {exc}",
        ) from exc
