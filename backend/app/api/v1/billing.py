"""Rotas de Billing, Planos, Assinaturas e Webhooks do Asaas."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.deps import BillingSvc, CurrentUser, DbSession
from app.core.config import settings
from app.models.user import User
from app.schemas.billing import (
    CheckoutIn,
    CheckoutOut,
    CouponValidateIn,
    CouponValidateOut,
    PlanOut,
    SubscriptionStatusOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
def list_plans() -> list[PlanOut]:
    """Lista todos os planos e ciclos de precificação vigentes com regras de inauguração."""
    from app.services.billing_service import BillingService

    return BillingService.get_plans()


@router.get("/status", response_model=SubscriptionStatusOut)
def get_subscription_status(
    current_user: CurrentUser,
    svc: BillingSvc,
) -> SubscriptionStatusOut:
    """Consulta o status da assinatura e dias restantes de trial da clínica logada."""
    if not current_user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não vinculado a uma clínica",
        )
    return svc.get_status(current_user.clinic_id)


@router.post("/coupons/validate", response_model=CouponValidateOut)
def validate_coupon(
    payload: CouponValidateIn,
    svc: BillingSvc,
) -> CouponValidateOut:
    """Valida um código de cupom de desconto para o ciclo escolhido."""
    return svc.validate_coupon(payload.code, payload.cycle)


@router.post("/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutIn,
    current_user: CurrentUser,
    svc: BillingSvc,
) -> CheckoutOut:
    """Gera intenção de assinatura via Asaas (Pix/Cartão/Boleto) preservando o trial."""
    if not current_user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não vinculado a uma clínica",
        )

    try:
        return svc.checkout(
            clinic_id=current_user.clinic_id,
            user_email=current_user.email,
            user_name=current_user.name,
            payload=payload,
        )
    except Exception as err:
        logger.exception("Erro ao processar checkout")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não foi possível iniciar o checkout: {err}",
        )


@router.post("/webhooks/asaas")
async def asaas_webhook(
    request: Request,
    asaas_access_token: Annotated[str | None, Header(alias="asaas-access-token")] = None,
) -> dict[str, str]:
    """Webhook do Asaas para recebimento e liquidação automática de assinaturas."""
    if settings.ASAAS_WEBHOOK_SECRET:
        if not asaas_access_token or asaas_access_token != settings.ASAAS_WEBHOOK_SECRET:
            logger.warning("Tentativa de webhook com token inválido ou ausente")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de webhook inválido",
            )

    body = await request.json()
    event = body.get("event")
    payment = body.get("payment", {})

    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Evento ausente")

    from app.db.session import unsafe_session_without_tenant
    from app.repositories.clinic import ClinicRepository
    from app.repositories.coupon_repository import CouponRepository
    from app.repositories.subscription_repository import SubscriptionRepository
    from app.services.billing_service import BillingService

    with unsafe_session_without_tenant("asaas webhook processing") as db:
        svc = BillingService(
            subscription_repo=SubscriptionRepository(db),
            coupon_repo=CouponRepository(db),
            clinic_repo=ClinicRepository(db),
        )
        svc.handle_asaas_webhook(event, payment)

    return {"status": "received"}
