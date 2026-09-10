"""Testes unitários do módulo centralizado de precificação (Billing)."""

from decimal import Decimal
import pytest

from app.domain.billing.pricing import (
    BillingCycle,
    LUMINA_PRO_PLAN,
    get_all_plans,
    get_cycle_pricing,
    get_plan,
)


def test_plan_lumina_pro_defaults():
    plan = get_plan("pro")
    assert plan.id == "pro"
    assert plan.trial_days == 14
    assert plan.is_launch_promo is True
    assert len(plan.features) >= 10


def test_pricing_cycles_amounts_and_savings():
    plan = get_plan("pro")

    # Mensal: R$ 80,00
    monthly = plan.cycles[BillingCycle.MONTHLY]
    assert monthly.months == 1
    assert monthly.monthly_equivalent == Decimal("80.00")
    assert monthly.total_amount == Decimal("80.00")
    assert monthly.savings_percentage == Decimal("0.00")

    # Trimestral: R$ 65,00/mês -> R$ 195,00
    quarterly = plan.cycles[BillingCycle.QUARTERLY]
    assert quarterly.months == 3
    assert quarterly.monthly_equivalent == Decimal("65.00")
    assert quarterly.total_amount == Decimal("195.00")
    assert quarterly.savings_percentage == Decimal("18.75")
    assert quarterly.badge == "Mais Escolhido"
    assert quarterly.is_featured is True

    # Anual: R$ 50,00/mês -> R$ 600,00
    yearly = plan.cycles[BillingCycle.YEARLY]
    assert yearly.months == 12
    assert yearly.monthly_equivalent == Decimal("50.00")
    assert yearly.total_amount == Decimal("600.00")
    assert yearly.savings_percentage == Decimal("37.50")
    assert "37%" in (yearly.badge or "")


def test_get_cycle_pricing_helper():
    pricing = get_cycle_pricing(BillingCycle.YEARLY)
    assert pricing.total_amount == Decimal("600.00")


def test_unknown_plan_raises_error():
    with pytest.raises(ValueError, match="Plano desconhecido"):
        get_plan("invalido")


def test_get_all_plans_returns_launch_plans():
    plans = get_all_plans()
    assert len(plans) == 1
    assert plans[0].id == "pro"
