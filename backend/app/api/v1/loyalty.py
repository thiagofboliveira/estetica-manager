from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.api.deps import LoyaltySvc
from app.schemas.loyalty import (
    LoyaltyAdjustRequest,
    LoyaltyOverviewOut,
    LoyaltyPatientOut,
    LoyaltyRewardCreate,
    LoyaltyRewardOut,
    LoyaltyRewardUpdate,
    LoyaltyTransactionOut,
    PublicVipCardOut,
    ReferralInfoOut,
    SendVipEmailResponse,
)
import logging
from app.services.loyalty_service import InsufficientPointsError, LoyaltyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


@router.get("/public-card/{code}", response_model=PublicVipCardOut)
def get_public_vip_card(code: str) -> PublicVipCardOut:
    """Rota pública para visualização do Cartão VIP digital da paciente (sem senha)."""
    try:
        return LoyaltyService.get_public_vip_card(code)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except Exception as exc:
        logger.exception("Erro ao buscar cartão VIP público para o código '%s': %s", code, exc)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Erro ao carregar Cartão VIP"
        ) from exc


@router.get("/overview", response_model=LoyaltyOverviewOut)
def get_loyalty_overview(svc: LoyaltySvc) -> LoyaltyOverviewOut:
    """Retorna métricas consolidadas do Clube VIP e Fidelidade da clínica."""
    return svc.get_overview()


@router.get("/rewards", response_model=list[LoyaltyRewardOut])
def list_rewards(
    svc: LoyaltySvc,
    active_only: bool = Query(False, description="Filtrar apenas recompensas ativas"),
) -> list[LoyaltyRewardOut]:
    """Lista as recompensas e benefícios do catálogo VIP da profissional."""
    return svc.list_rewards(active_only=active_only)


@router.post("/rewards", response_model=LoyaltyRewardOut, status_code=status.HTTP_201_CREATED)
def create_reward(payload: LoyaltyRewardCreate, svc: LoyaltySvc) -> LoyaltyRewardOut:
    """Cria uma nova recompensa no catálogo VIP."""
    try:
        return svc.create_reward(payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.put("/rewards/{reward_id}", response_model=LoyaltyRewardOut)
def update_reward(
    reward_id: UUID, payload: LoyaltyRewardUpdate, svc: LoyaltySvc
) -> LoyaltyRewardOut:
    """Atualiza uma recompensa existente no catálogo VIP."""
    try:
        return svc.update_reward(reward_id, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.delete("/rewards/{reward_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reward(reward_id: UUID, svc: LoyaltySvc) -> Response:
    """Remove uma recompensa do catálogo VIP."""
    try:
        svc.delete_reward(reward_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/patients/{patient_id}", response_model=LoyaltyPatientOut)
def get_patient_loyalty(patient_id: UUID, svc: LoyaltySvc) -> LoyaltyPatientOut:
    """Retorna o extrato de fidelidade, nível VIP e saldo de pontos do paciente."""
    try:
        return svc.get_patient_loyalty(patient_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/patients/{patient_id}/adjust", response_model=LoyaltyTransactionOut)
def adjust_patient_points(
    patient_id: UUID, payload: LoyaltyAdjustRequest, svc: LoyaltySvc
) -> LoyaltyTransactionOut:
    """Realiza ajuste manual de pontos (crédito bônus ou débito por resgate em procedimento)."""
    try:
        return svc.adjust_points(patient_id, payload)
    except InsufficientPointsError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/patients/{patient_id}/referral", response_model=ReferralInfoOut)
def get_patient_referral_info(patient_id: UUID, svc: LoyaltySvc) -> ReferralInfoOut:
    """Retorna link de indicação 'Traga uma Amiga' com WhatsApp e lista de amigas convertidas."""
    try:
        return svc.get_referral_info(patient_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/patients/{patient_id}/send-card-email", response_model=SendVipEmailResponse)
def send_patient_vip_email(
    patient_id: UUID,
    request: Request,
    svc: LoyaltySvc,
) -> SendVipEmailResponse:
    """Dispara por e-mail o Cartão VIP digital da paciente com link sem senha."""
    try:
        origin = request.headers.get("origin") or str(request.base_url).rstrip("/")
        return svc.send_vip_card_email(patient_id, app_base_url=origin)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


