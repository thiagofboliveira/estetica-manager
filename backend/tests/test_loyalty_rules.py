from decimal import Decimal
from app.domain.loyalty.rules import (
    VipTier,
    calculate_earned_points,
    determine_vip_tier,
    generate_referral_code,
)


def test_calculate_earned_points():
    assert calculate_earned_points(Decimal("100.00"), Decimal("0.10")) == 10
    assert calculate_earned_points(Decimal("350.50"), Decimal("0.10")) == 35
    assert calculate_earned_points(Decimal("0.00"), Decimal("0.10")) == 0
    assert calculate_earned_points(Decimal("-50.00"), Decimal("0.10")) == 0
    # Custom rate: 1 pt every R$ 5 (0.20)
    assert calculate_earned_points(Decimal("100.00"), Decimal("0.20")) == 20


def test_determine_vip_tier():
    assert determine_vip_tier(0) == VipTier.BRONZE
    assert determine_vip_tier(99) == VipTier.BRONZE
    assert determine_vip_tier(100) == VipTier.SILVER
    assert determine_vip_tier(299) == VipTier.SILVER
    assert determine_vip_tier(300) == VipTier.GOLD
    assert determine_vip_tier(699) == VipTier.GOLD
    assert determine_vip_tier(700) == VipTier.DIAMOND
    assert determine_vip_tier(1500) == VipTier.DIAMOND


def test_generate_referral_code():
    code1 = generate_referral_code("Mariana Silva")
    assert code1.startswith("MAR-")
    assert len(code1) == 8

    code2 = generate_referral_code(None)
    assert code2.startswith("VIP-")
    assert len(code2) == 8
