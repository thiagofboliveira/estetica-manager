"""Módulo Centralizado de Preços e Regras de Negócio de Assinaturas (Billing).

Fonte Única da Verdade (Single Source of Truth) para novos planos, ciclos,
período de teste e promoções de inauguração.
Puro: sem SQLAlchemy, sem FastAPI, sem I/O.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class BillingCycle(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


@dataclass(frozen=True)
class PlanCyclePricing:
    cycle: BillingCycle
    months: int
    monthly_equivalent: Decimal
    total_amount: Decimal
    savings_percentage: Decimal
    badge: str | None
    is_featured: bool


@dataclass(frozen=True)
class PlanDefinition:
    id: str
    name: str
    description: str
    trial_days: int
    is_launch_promo: bool
    promo_headline: str
    promo_badge: str
    features: tuple[str, ...]
    cycles: dict[BillingCycle, PlanCyclePricing]


# Configuração Centralizada de Preços da Promoção de Inauguração
TRIAL_DAYS_DEFAULT = 14

# Valores base mensais equivalentes acordados:
# Mensal: R$ 80,00 / mês
# Trimestral: R$ 65,00 / mês (R$ 195,00 a cada 3 meses)
# Anual: R$ 50,00 / mês (R$ 600,00 por ano)
_MONTHLY_BASE = Decimal("80.00")
_QUARTERLY_MONTHLY = Decimal("65.00")
_YEARLY_MONTHLY = Decimal("50.00")

_QUARTERLY_TOTAL = (_QUARTERLY_MONTHLY * Decimal("3")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # R$ 195.00
_YEARLY_TOTAL = (_YEARLY_MONTHLY * Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)      # R$ 600.00

# Economias relativas contra a cobrança mensal plena:
# Trimestral: 1 - (195 / (80 * 3)) = 1 - (195 / 240) = 18.75%
_QUARTERLY_SAVINGS = (
    (Decimal("1") - (_QUARTERLY_TOTAL / (Decimal("3") * _MONTHLY_BASE))) * Decimal("100")
).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# Anual: 1 - (600 / (80 * 12)) = 1 - (600 / 960) = 37.50%
_YEARLY_SAVINGS = (
    (Decimal("1") - (_YEARLY_TOTAL / (Decimal("12") * _MONTHLY_BASE))) * Decimal("100")
).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


LUMINA_PRO_PLAN = PlanDefinition(
    id="pro",
    name="Lumina Pro",
    description="Acesso completo a todas as funcionalidades de gestão financeira, lucro real e retenção.",
    trial_days=TRIAL_DAYS_DEFAULT,
    is_launch_promo=True,
    promo_headline="Promoção Especial de Inauguração — Garanta sua vaga com preço travado",
    promo_badge="Promoção de Inauguração",
    features=(
        "Cálculo de Lucro Real com 5 modelos contábeis",
        "Motor de Retenção Ativa ('Quem devo chamar hoje?')",
        "Disparos personalizados para WhatsApp com 1 clique",
        "Agenda inteligente com confirmação anti-no-show",
        "Modo Ocupado (WhatsApp Rápido com horários vagos)",
        "Agendamento público na bio do Instagram",
        "Prontuário completo com fotos Antes & Depois (LGPD)",
        "Anamnese digital com assinatura eletrônica na tela",
        "Controle de insumos e rastreamento de frascos de Botox",
        "Gestão de custos fixos e cálculo de Ponto de Equilíbrio (Breakeven)",
        "Relatórios analíticos completos e exportação em CSV",
    ),
    cycles={
        BillingCycle.MONTHLY: PlanCyclePricing(
            cycle=BillingCycle.MONTHLY,
            months=1,
            monthly_equivalent=_MONTHLY_BASE,
            total_amount=_MONTHLY_BASE,
            savings_percentage=Decimal("0.00"),
            badge=None,
            is_featured=False,
        ),
        BillingCycle.QUARTERLY: PlanCyclePricing(
            cycle=BillingCycle.QUARTERLY,
            months=3,
            monthly_equivalent=_QUARTERLY_MONTHLY,
            total_amount=_QUARTERLY_TOTAL,
            savings_percentage=_QUARTERLY_SAVINGS,
            badge="Mais Escolhido",
            is_featured=True,
        ),
        BillingCycle.YEARLY: PlanCyclePricing(
            cycle=BillingCycle.YEARLY,
            months=12,
            monthly_equivalent=_YEARLY_MONTHLY,
            total_amount=_YEARLY_TOTAL,
            savings_percentage=_YEARLY_SAVINGS,
            badge="Maior Economia (37% OFF)",
            is_featured=False,
        ),
    },
)


def get_plan(plan_id: str = "pro") -> PlanDefinition:
    """Retorna a definição do plano pelo identificador."""
    if plan_id == "pro":
        return LUMINA_PRO_PLAN
    raise ValueError(f"Plano desconhecido: {plan_id}")


def get_all_plans() -> list[PlanDefinition]:
    """Retorna a lista de planos vigentes para contratação."""
    return [LUMINA_PRO_PLAN]


def get_cycle_pricing(cycle: BillingCycle, plan_id: str = "pro") -> PlanCyclePricing:
    """Recupera os detalhes de precificação de um ciclo específico."""
    plan = get_plan(plan_id)
    if cycle not in plan.cycles:
        raise ValueError(f"Ciclo {cycle} não suportado para o plano {plan_id}")
    return plan.cycles[cycle]
