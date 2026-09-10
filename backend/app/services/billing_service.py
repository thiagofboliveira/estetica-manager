"""Serviço de Aplicação para Gestão de Billing, Assinaturas e Webhooks."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from uuid import UUID, uuid4

from app.core.asaas import AsaasClient
from app.domain.billing.coupons import (
    CouponEvaluation,
    CouponValidationError,
    apply_coupon,
)
from app.domain.billing.pricing import (
    BillingCycle,
    get_all_plans,
    get_cycle_pricing,
    get_plan,
)
from app.models.clinic import Clinic
from app.models.subscription import Subscription, SubscriptionStatus
from app.repositories.clinic import ClinicRepository
from app.repositories.coupon_repository import CouponRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.billing import (
    CheckoutIn,
    CheckoutOut,
    CouponValidateOut,
    PlanCycleOut,
    PlanOut,
    SubscriptionStatusOut,
)

logger = logging.getLogger(__name__)


class BillingService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        coupon_repo: CouponRepository,
        clinic_repo: ClinicRepository,
        asaas_client: AsaasClient | None = None,
    ) -> None:
        self._sub_repo = subscription_repo
        self._coupon_repo = coupon_repo
        self._clinic_repo = clinic_repo
        self._asaas = asaas_client or AsaasClient()

    @staticmethod
    def get_plans() -> list[PlanOut]:
        """Retorna todos os planos e ciclos de precificação centralizados."""
        plans = get_all_plans()
        result = []
        for p in plans:
            cycles_out = [
                PlanCycleOut(
                    cycle=cp.cycle,
                    months=cp.months,
                    monthly_equivalent=str(cp.monthly_equivalent),
                    total_amount=str(cp.total_amount),
                    savings_percentage=str(cp.savings_percentage),
                    badge=cp.badge,
                    is_featured=cp.is_featured,
                )
                for cp in p.cycles.values()
            ]
            result.append(
                PlanOut(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    trial_days=p.trial_days,
                    is_launch_promo=p.is_launch_promo,
                    promo_headline=p.promo_headline,
                    promo_badge=p.promo_badge,
                    features=list(p.features),
                    cycles=cycles_out,
                )
            )
        return result

    def get_or_create_subscription(self, clinic_id: UUID) -> Subscription:
        """Garante que a clínica possua uma assinatura/trial ativa."""
        sub = self._sub_repo.get_by_clinic_id(clinic_id)
        if sub:
            # Atualiza status se o trial já passou
            now = datetime.now(timezone.utc)
            if sub.status in (SubscriptionStatus.TRIALING, SubscriptionStatus.TRIALING.value) and now > sub.trial_ends_at:
                sub.status = SubscriptionStatus.EXPIRED.value
                self._sub_repo.flush()
            return sub

        clinic = self._clinic_repo.get_by_id(clinic_id)
        now = datetime.now(timezone.utc)
        trial_start = clinic.created_at if clinic and clinic.created_at else now
        trial_end = trial_start + timedelta(days=14)
        status = SubscriptionStatus.TRIALING if now <= trial_end else SubscriptionStatus.EXPIRED

        sub = Subscription(
            id=uuid4(),
            clinic_id=clinic_id,
            plan_id="pro",
            cycle=BillingCycle.MONTHLY,
            status=status,
            amount=Decimal("80.00"),
            trial_started_at=trial_start,
            trial_ends_at=trial_end,
        )
        return self._sub_repo.add(sub)

    def get_status(self, clinic_id: UUID) -> SubscriptionStatusOut:
        """Retorna o estado da assinatura da clínica para a UI e guards."""
        sub = self.get_or_create_subscription(clinic_id)
        now = datetime.now(timezone.utc)

        days_left = max(0, (sub.trial_ends_at - now).days)
        is_trial_active = (
            sub.status in (SubscriptionStatus.TRIALING, SubscriptionStatus.TRIALING.value)
            and now <= sub.trial_ends_at
        )
        is_subscription_active = (
            sub.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE.value)
            or is_trial_active
        )

        status_str = sub.status.value if hasattr(sub.status, "value") else str(sub.status)
        cycle_val = sub.cycle if isinstance(sub.cycle, BillingCycle) else BillingCycle(str(sub.cycle))

        return SubscriptionStatusOut(
            status=status_str,
            plan_id=sub.plan_id,
            cycle=cycle_val,
            amount=str(sub.amount),
            trial_started_at=sub.trial_started_at,
            trial_ends_at=sub.trial_ends_at,
            days_left_in_trial=days_left,
            is_trial_active=is_trial_active,
            is_subscription_active=is_subscription_active,
            current_period_start=sub.current_period_start,
            current_period_end=sub.current_period_end,
            invoice_url=sub.invoice_url,
        )

    def validate_coupon(self, code: str, cycle: BillingCycle) -> CouponValidateOut:
        """Valida se o cupom existe e é elegível para o ciclo solicitado."""
        cycle_pricing = get_cycle_pricing(cycle)
        coupon = self._coupon_repo.get_by_code(code)
        if not coupon:
            return CouponValidateOut(
                is_valid=False,
                code=code.upper(),
                original_amount=str(cycle_pricing.total_amount),
                discount_amount="0.00",
                final_amount=str(cycle_pricing.total_amount),
                savings_percentage="0.00",
                message="Cupom não encontrado.",
            )

        allowed = None
        if coupon.allowed_cycles:
            allowed = tuple(
                BillingCycle(c.strip())
                for c in coupon.allowed_cycles.split(",")
                if c.strip() in BillingCycle._value2member_map_
            )

        try:
            evaluation = apply_coupon(
                code=coupon.code,
                discount_type=coupon.discount_type,
                discount_value=coupon.discount_value,
                base_amount=cycle_pricing.total_amount,
                cycle=cycle,
                is_active=coupon.is_active,
                valid_from=coupon.valid_from,
                valid_until=coupon.valid_until,
                max_redemptions=coupon.max_redemptions,
                times_redeemed=coupon.times_redeemed,
                allowed_cycles=allowed,
            )
            discount_type_str = (
                evaluation.discount_type.value
                if hasattr(evaluation.discount_type, "value")
                else str(evaluation.discount_type)
            )
            return CouponValidateOut(
                is_valid=True,
                code=evaluation.code,
                discount_type=discount_type_str,
                original_amount=str(evaluation.original_amount),
                discount_amount=str(evaluation.discount_amount),
                final_amount=str(evaluation.final_amount),
                savings_percentage=str(evaluation.savings_percentage),
                message="Cupom aplicado com sucesso!",
            )
        except CouponValidationError as err:
            return CouponValidateOut(
                is_valid=False,
                code=code.upper(),
                original_amount=str(cycle_pricing.total_amount),
                discount_amount="0.00",
                final_amount=str(cycle_pricing.total_amount),
                savings_percentage="0.00",
                message=str(err),
            )

    def checkout(
        self,
        clinic_id: UUID,
        user_email: str,
        user_name: str,
        payload: CheckoutIn,
    ) -> CheckoutOut:
        """Processa a intenção de contratação, integrando com o Asaas."""
        clinic = self._clinic_repo.get_by_id(clinic_id)
        if not clinic:
            raise LookupError("Clínica não encontrada")

        sub = self.get_or_create_subscription(clinic_id)
        pricing = get_cycle_pricing(payload.cycle)
        final_amount = pricing.total_amount
        coupon_id = None

        if payload.coupon_code:
            coupon = self._coupon_repo.get_by_code(payload.coupon_code)
            if coupon:
                val_res = self.validate_coupon(payload.coupon_code, payload.cycle)
                if val_res.is_valid:
                    final_amount = Decimal(val_res.final_amount)
                    coupon_id = coupon.id
                    self._coupon_repo.increment_redemption(coupon.id)

        # Determina a data do primeiro vencimento:
        # Se ainda está em trial, preserva os dias grátis restantes!
        now = datetime.now(timezone.utc)
        is_trial_active = now < sub.trial_ends_at
        if is_trial_active:
            first_due_date = sub.trial_ends_at.date()
        else:
            # Vence amanhã se o trial já acabou
            first_due_date = (now + timedelta(days=1)).date()

        # 1. Cria ou recupera cliente no Asaas
        customer_doc = payload.document or clinic.document
        customer_phone = payload.phone or clinic.phone
        asaas_customer_id = self._asaas.create_or_get_customer(
            name=clinic.name or user_name,
            email=user_email,
            cpf_cnpj=customer_doc,
            phone=customer_phone,
        )

        # 2. Cria a assinatura no Asaas
        description = f"Lumina Pro — Plano {payload.cycle.value}"
        asaas_sub = self._asaas.create_subscription(
            customer_id=asaas_customer_id,
            value=final_amount,
            cycle=payload.cycle,
            next_due_date=first_due_date,
            billing_type=payload.billing_type,
            description=description,
        )

        # 3. Atualiza registro local
        sub.cycle = payload.cycle
        sub.amount = final_amount
        sub.asaas_customer_id = asaas_customer_id
        sub.asaas_subscription_id = asaas_sub.get("id")
        sub.coupon_id = coupon_id
        sub.payment_method = payload.billing_type
        sub.invoice_url = asaas_sub.get("invoiceUrl")
        self._sub_repo.flush()

        status_str = sub.status.value if hasattr(sub.status, "value") else str(sub.status)
        return CheckoutOut(
            subscription_id=str(sub.id),
            status=status_str,
            amount=str(final_amount),
            cycle=payload.cycle,
            invoice_url=sub.invoice_url,
            pix_qrcode_payload=sub.pix_qrcode_payload,
            first_due_date=first_due_date.isoformat(),
            is_trial_included=is_trial_active,
        )

    def handle_asaas_webhook(self, event: str, payment_data: dict) -> None:
        """Processa eventos de liquidação e cancelamento recebidos do Asaas."""
        logger.info("Processando webhook Asaas: evento=%s", event)
        asaas_sub_id = payment_data.get("subscription")
        customer_id = payment_data.get("customer")

        sub = None
        if asaas_sub_id:
            sub = self._sub_repo.get_by_asaas_subscription_id(str(asaas_sub_id))
        if not sub and customer_id:
            sub = self._sub_repo.get_by_asaas_customer_id(str(customer_id))

        if not sub:
            logger.warning("Assinatura não encontrada para webhook Asaas: sub=%s, cus=%s", asaas_sub_id, customer_id)
            return

        now = datetime.now(timezone.utc)

        if event in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
            sub.status = SubscriptionStatus.ACTIVE.value
            sub.current_period_start = now
            months_to_add = 1
            if sub.cycle in (BillingCycle.QUARTERLY, BillingCycle.QUARTERLY.value):
                months_to_add = 3
            elif sub.cycle in (BillingCycle.YEARLY, BillingCycle.YEARLY.value):
                months_to_add = 12
            # Aproximação mensal de 30 dias
            sub.current_period_end = now + timedelta(days=30 * months_to_add)
            if payment_data.get("invoiceUrl"):
                sub.invoice_url = payment_data["invoiceUrl"]
            logger.info("Assinatura %s ativada com sucesso até %s", sub.id, sub.current_period_end)

        elif event == "PAYMENT_OVERDUE":
            # Concede 2 dias de tolerância antes de travar
            sub.status = SubscriptionStatus.PAST_DUE.value
            logger.info("Assinatura %s marcada como PAST_DUE", sub.id)

        elif event in ("SUBSCRIPTION_DELETED", "PAYMENT_REFUNDED"):
            sub.status = SubscriptionStatus.CANCELED.value
            logger.info("Assinatura %s cancelada", sub.id)

        self._sub_repo.flush()
