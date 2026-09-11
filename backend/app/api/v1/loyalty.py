from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import LoyaltySvc
from app.schemas.loyalty import (
    LoyaltyAdjustRequest,
    LoyaltyOverviewOut,
    LoyaltyPatientOut,
    LoyaltyTransactionOut,
    ReferralInfoOut,
)
from app.services.loyalty_service import InsufficientPointsError

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


@router.get("/overview", response_model=LoyaltyOverviewOut)
def get_loyalty_overview(svc: LoyaltySvc) -> LoyaltyOverviewOut:
    """Retorna métricas consolidadas do Clube VIP e Fidelidade da clínica."""
    return svc.get_overview()


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
