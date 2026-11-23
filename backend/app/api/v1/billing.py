"""Rotas de Billing, Planos, Assinaturas e Webhooks do Asaas."""

import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.api.deps import BillingSvc, CouponValidateRateLimit, CurrentUser
from app.core.config import settings
from app.schemas.billing import (
    CheckoutIn,
    CheckoutOut,
    CouponValidateIn,
    CouponValidateOut,
    PlanOut,
    SubscriptionStatusOut,
)
from app.services.billing_service import CheckoutConflictError

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
    _rate_limit: CouponValidateRateLimit,
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
    except CheckoutConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(err)
        ) from err
    except Exception as err:
        # Detalhe técnico fica só no log: devolver str(err) ao cliente vaza
        # resposta crua do gateway e mensagens internas.
        logger.exception("Erro ao processar checkout")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível iniciar o checkout. Tente novamente em instantes.",
        ) from err


@router.post("/webhooks/asaas")
async def asaas_webhook(
    request: Request,
    asaas_access_token: Annotated[str | None, Header(alias="asaas-access-token")] = None,
) -> dict[str, str]:
    """Webhook do Asaas para recebimento e liquidação automática de assinaturas."""
    secret = settings.ASAAS_WEBHOOK_SECRET
    if not secret:
        # Fail-closed: sem segredo configurado qualquer um poderia forjar
        # "pagamento confirmado" e ativar assinatura de graça.
        logger.error("ASAAS_WEBHOOK_SECRET não configurado — webhook recusado")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook não configurado",
        )
    if not asaas_access_token or not hmac.compare_digest(
        asaas_access_token.encode(), secret.encode()
    ):
        logger.warning("Tentativa de webhook com token inválido ou ausente")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de webhook inválido",
        )

    try:
        body = await request.json()
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Corpo inválido"
        ) from err
    if not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Corpo inválido"
        )
    event = body.get("event")
    payment = body.get("payment") or {}

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
