from decimal import Decimal
from enum import StrEnum
import math
import secrets
import string


class VipTier(StrEnum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    DIAMOND = "DIAMOND"


VIP_TIER_CONFIG = {
    VipTier.BRONZE: {
        "name": "Bronze",
        "badge": "🥉",
        "min_points": 0,
        "discount_percent": Decimal("0.00"),
        "color": "#b45309",
        "bg_color": "#fef3c7",
    },
    VipTier.SILVER: {
        "name": "Prata",
        "badge": "🥈",
        "min_points": 100,
        "discount_percent": Decimal("0.05"),
        "color": "#475569",
        "bg_color": "#f1f5f9",
    },
    VipTier.GOLD: {
        "name": "Ouro",
        "badge": "🥇",
        "min_points": 300,
        "discount_percent": Decimal("0.10"),
        "color": "#d97706",
        "bg_color": "#fef9c3",
    },
    VipTier.DIAMOND: {
        "name": "Diamante VIP",
        "badge": "💎",
        "min_points": 700,
        "discount_percent": Decimal("0.15"),
        "color": "#0284c7",
        "bg_color": "#e0f2fe",
    },
}


def calculate_earned_points(gross_amount: Decimal, points_per_currency: Decimal) -> int:
    """Calcula pontos acumulados em uma venda.
    Ex: R$ 350,00 * 0.10 = 35 pontos."""
    if gross_amount <= Decimal("0.00") or points_per_currency <= Decimal("0.00"):
        return 0
    return int(math.floor(gross_amount * points_per_currency))


def determine_vip_tier(cumulative_points: int) -> VipTier:
    """Determina a categoria VIP com base nos pontos acumulados do paciente."""
    if cumulative_points >= 700:
        return VipTier.DIAMOND
    if cumulative_points >= 300:
        return VipTier.GOLD
    if cumulative_points >= 100:
        return VipTier.SILVER
    return VipTier.BRONZE


def generate_referral_code(patient_name: str | None = None) -> str:
    """Gera um código legível e amigável para indicação.
    Ex: ANA-4820 ou VIP-7391"""
    prefix = "VIP"
    if patient_name and len(patient_name.strip()) >= 3:
        clean_prefix = "".join(c for c in patient_name.upper() if c in string.ascii_uppercase)
        if len(clean_prefix) >= 3:
            prefix = clean_prefix[:3]
    digits = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"{prefix}-{digits}"
