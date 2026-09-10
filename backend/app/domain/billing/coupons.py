"""Módulo de Domínio para Validação e Aplicação de Cupons de Desconto.

Puro: sem SQLAlchemy, sem FastAPI, sem I/O.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from app.domain.billing.pricing import BillingCycle


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


class CouponValidationError(Exception):
    """Erro de validação ou inelegibilidade do cupom."""
    pass


@dataclass(frozen=True)
class CouponEvaluation:
    code: str
    discount_type: DiscountType
    discount_value: Decimal
    original_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    savings_percentage: Decimal


def apply_coupon(
    code: str,
    discount_type: DiscountType,
    discount_value: Decimal,
    base_amount: Decimal,
    cycle: BillingCycle,
    is_active: bool = True,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    max_redemptions: int | None = None,
    times_redeemed: int = 0,
    allowed_cycles: tuple[BillingCycle, ...] | None = None,
    now: datetime | None = None,
) -> CouponEvaluation:
    """Valida as condições do cupom e calcula o valor final com arredondamento contábil."""
    if not is_active:
        raise CouponValidationError("Cupom inativo ou desativado")

    current_time = now or datetime.now(timezone.utc)

    if valid_from and current_time < valid_from:
        raise CouponValidationError("Cupom ainda não está vigente")

    if valid_until and current_time > valid_until:
        raise CouponValidationError("Cupom expirado")

    if max_redemptions is not None and times_redeemed >= max_redemptions:
        raise CouponValidationError("Limite máximo de usos deste cupom foi atingido")

    if allowed_cycles and cycle not in allowed_cycles:
        cycles_str = ", ".join(c.value for c in allowed_cycles)
        raise CouponValidationError(f"Cupom válido apenas para os ciclos: {cycles_str}")

    if discount_type == DiscountType.PERCENTAGE:
        if discount_value < Decimal("0.00") or discount_value > Decimal("100.00"):
            raise CouponValidationError("Percentual de desconto inválido")
        discount_amount = (base_amount * (discount_value / Decimal("100.00"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    elif discount_type == DiscountType.FIXED:
        if discount_value < Decimal("0.00"):
            raise CouponValidationError("Valor fixo de desconto inválido")
        discount_amount = min(base_amount, discount_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    else:
        raise CouponValidationError(f"Tipo de desconto não suportado: {discount_type}")

    final_amount = max(Decimal("0.00"), base_amount - discount_amount).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    savings_percentage = (
        ((discount_amount / base_amount) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if base_amount > Decimal("0.00")
        else Decimal("0.00")
    )

    return CouponEvaluation(
        code=code.strip().upper(),
        discount_type=discount_type,
        discount_value=discount_value,
        original_amount=base_amount,
        discount_amount=discount_amount,
        final_amount=final_amount,
        savings_percentage=savings_percentage,
    )
