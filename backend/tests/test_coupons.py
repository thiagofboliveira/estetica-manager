"""Testes unitários da lógica de cupons de desconto."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.domain.billing.coupons import (
    CouponValidationError,
    DiscountType,
    apply_coupon,
)
from app.domain.billing.pricing import BillingCycle


def test_apply_percentage_coupon():
    eval_res = apply_coupon(
        code="PROMO10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10.00"),
        base_amount=Decimal("600.00"),
        cycle=BillingCycle.YEARLY,
    )
    assert eval_res.code == "PROMO10"
    assert eval_res.original_amount == Decimal("600.00")
    assert eval_res.discount_amount == Decimal("60.00")
    assert eval_res.final_amount == Decimal("540.00")
    assert eval_res.savings_percentage == Decimal("10.00")


def test_apply_fixed_coupon():
    eval_res = apply_coupon(
        code="VALE30",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("30.00"),
        base_amount=Decimal("80.00"),
        cycle=BillingCycle.MONTHLY,
    )
    assert eval_res.discount_amount == Decimal("30.00")
    assert eval_res.final_amount == Decimal("50.00")


def test_fixed_coupon_larger_than_amount():
    eval_res = apply_coupon(
        code="SUPER100",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("100.00"),
        base_amount=Decimal("80.00"),
        cycle=BillingCycle.MONTHLY,
    )
    assert eval_res.discount_amount == Decimal("80.00")
    assert eval_res.final_amount == Decimal("0.00")


def test_inactive_coupon_rejected():
    with pytest.raises(CouponValidationError, match="Cupom inativo"):
        apply_coupon(
            code="INATIVO",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            base_amount=Decimal("80.00"),
            cycle=BillingCycle.MONTHLY,
            is_active=False,
        )


def test_expired_coupon_rejected():
    past = datetime.now(timezone.utc) - timedelta(days=2)
    with pytest.raises(CouponValidationError, match="Cupom expirado"):
        apply_coupon(
            code="EXPIRADO",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            base_amount=Decimal("80.00"),
            cycle=BillingCycle.MONTHLY,
            valid_until=past,
        )


def test_max_redemptions_reached_rejected():
    with pytest.raises(CouponValidationError, match="Limite máximo de usos"):
        apply_coupon(
            code="ESGOTADO",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            base_amount=Decimal("80.00"),
            cycle=BillingCycle.MONTHLY,
            max_redemptions=5,
            times_redeemed=5,
        )


def test_allowed_cycles_restriction():
    with pytest.raises(CouponValidationError, match="Cupom válido apenas para os ciclos"):
        apply_coupon(
            code="APENASANUAL",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("15.00"),
            base_amount=Decimal("80.00"),
            cycle=BillingCycle.MONTHLY,
            allowed_cycles=(BillingCycle.YEARLY,),
        )
