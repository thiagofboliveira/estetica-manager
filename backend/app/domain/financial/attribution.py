"""Módulo de Atribuição de Receita Recuperada (EPIC-S2-01, MVP v6 §15.2).

Calcula a Receita Mensal Atribuível ao Sistema (RMAS) seguindo critérios conservadores:
- Janela de até 21 dias entre o contato e a venda.
- Oportunidade com timing OVERDUE no momento do contato (due_date < contacted_at - 7 dias).
- Sem dupla contagem de vendas (resolved_by_sale_id único).
- Invariante I1: Todos os cálculos em Decimal com arredondamento ROUND_HALF_UP.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.core.money import money


@dataclass(frozen=True)
class AttributedCandidate:
    opportunity_id: UUID
    patient_id: UUID
    due_date: date
    contacted_at: datetime | None
    resolved_by_sale_id: UUID | None
    sale_sold_at: datetime | None
    sale_net_profit: Decimal | None


@dataclass(frozen=True)
class AttributionResult:
    attributed_revenue: Decimal
    attributed_sale_count: int
    patients_reactivated: int
    subscription_fee: Decimal
    roi_ratio: Decimal | None


def calculate_attributed_revenue(
    candidates: list[AttributedCandidate],
    subscription_fee: Decimal = Decimal("97.00"),
) -> AttributionResult:
    """Calcula a receita recuperada atribuível ao sistema de forma pura."""
    attributed_sales: dict[UUID, Decimal] = {}
    reactivated_patients: set[UUID] = set()

    for item in candidates:
        if not item.contacted_at or not item.resolved_by_sale_id or not item.sale_sold_at:
            continue

        # Janela de atribuição de 21 dias (contacted_at <= sold_at <= contacted_at + 21d)
        contact_date = item.contacted_at.date() if isinstance(item.contacted_at, datetime) else item.contacted_at
        sale_date = item.sale_sold_at.date() if isinstance(item.sale_sold_at, datetime) else item.sale_sold_at

        if sale_date < contact_date:
            continue
        if sale_date > contact_date + timedelta(days=21):
            continue

        # Apenas oportunidades que estavam OVERDUE no momento do contato (due_date < contact_date - 7 dias)
        # Margem de tolerância da janela ideal: 7 dias de atraso caracteriza OVERDUE (MVP §11)
        if item.due_date >= contact_date - timedelta(days=7):
            continue

        sale_id = item.resolved_by_sale_id
        profit = money(item.sale_net_profit) if item.sale_net_profit is not None else Decimal("0.00")

        # Deduplicação: se a mesma venda resolveu mais de uma oportunidade, conta o lucro apenas 1 vez
        if sale_id not in attributed_sales:
            attributed_sales[sale_id] = profit
        reactivated_patients.add(item.patient_id)

    total_revenue = money(sum(attributed_sales.values(), Decimal("0.00")))
    sale_count = len(attributed_sales)
    patient_count = len(reactivated_patients)

    roi: Decimal | None = None
    if subscription_fee > Decimal("0.00"):
        roi = (total_revenue / subscription_fee).quantize(Decimal("0.1"))

    return AttributionResult(
        attributed_revenue=total_revenue,
        attributed_sale_count=sale_count,
        patients_reactivated=patient_count,
        subscription_fee=money(subscription_fee),
        roi_ratio=roi,
    )
