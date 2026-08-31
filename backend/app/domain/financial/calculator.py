"""Motor de lucro real (MVP v6 §12, TASK-018/019/020).

PURO: sem SQLAlchemy, sem FastAPI, sem I/O (backend/ENGENHARIA.md §5).
Testável em milissegundos, sem banco. `app/domain/` não importa nada de
`models`/`schemas`/`sqlalchemy` — garantido por
tests/test_architecture.py::test_dominio_nao_importa_infraestrutura.

Fórmula parametrizada exata (§12, TASK-018):

    items_total  = Σ (item.unit_price × item.quantity)
    bruto        = items_total − discount_amount
    taxa         = f(payment_method, installments, payment_fee_rules, antecipação)
    base_split   = bruto              se split_base = GROSS
                 = bruto − taxa       se split_base = NET_OF_FEE
    split        = base_split × split_clinic_percentage (ou split_override por item)
    taxa_dela    = taxa                  se fee_payer = PROFESSIONAL
                 = 0                     se fee_payer = CLINIC
                 = taxa × (1 − split%)   se fee_payer = SPLIT_PRO_RATA
    (fee_payer se aplica sempre, independente de split_base — são eixos
     ortogonais, E1 e E2. Ver TASK-044 no MVP para a matriz de 5 cenários
     que prova isto.)
    custo        = Σ por sessão: COALESCE(session.cost_override,
                                           item.unit_cost_estimated)
                   exceto sessões EXPIRED
    lucro_real   = bruto − split − taxa_dela − custo

Duas decisões de arredondamento (backend/ENGENHARIA.md §5):
  1) Taxa: calcula o TOTAL e rateia — não calcula por item e soma. Somar
     N arredondamentos diverge da taxa que a adquirente cobra sobre o
     total.
  2) net_profit é resultado de subtrações encadeadas do TOTAL da venda,
     não soma de resultados por item — garante que o cabeçalho nunca
     contradiz o detalhamento.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

from app.core.money import ZERO, allocate, apply_rate, money


class SplitBase(StrEnum):
    GROSS = "GROSS"
    NET_OF_FEE = "NET_OF_FEE"


class FeePayer(StrEnum):
    PROFESSIONAL = "PROFESSIONAL"
    CLINIC = "CLINIC"
    SPLIT_PRO_RATA = "SPLIT_PRO_RATA"


class PaymentMethod(StrEnum):
    PIX = "PIX"
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    CASH = "CASH"
    TRANSFER = "TRANSFER"


@dataclass(frozen=True)
class LineItem:
    """Um SaleItem, na visão pura do motor. unit_price/unit_cost_estimated
    já vêm congelados (snapshot do Procedure) — o motor não sabe de onde
    vieram."""

    unit_price: Decimal
    quantity: int
    unit_cost_estimated: Decimal
    # Custo por sessão já resolvido (COALESCE cost_override, se houver) e
    # já excluindo sessões EXPIRED — ver `provisioned_cost`/`realized_cost`.
    session_costs: list[Decimal]
    # E6 — split_override por procedimento (P1)
    split_override: Decimal | None = None


@dataclass(frozen=True)
class FeeRule:
    installments_min: int
    installments_max: int
    fee_percentage: Decimal  # ex: Decimal("5.00") == 5%
    fixed_fee: Decimal = ZERO


@dataclass(frozen=True)
class SaleParams:
    split_clinic_percentage: Decimal  # ex: Decimal("30.00") == 30%
    split_base: SplitBase
    fee_payer: FeePayer
    payment_method: PaymentMethod
    installments: int
    discount_amount: Decimal
    fee_rules: list[FeeRule]
    # E7 — Antecipação de Recebíveis (P1)
    anticipates_all: bool = False
    anticipation_rate_per_installment: Decimal | None = None


@dataclass(frozen=True)
class ItemCalculationResult:
    unit_price: Decimal
    quantity: int
    line_total: Decimal  # unit_price * quantity, antes do desconto
    discount_allocated: Decimal
    net_of_discount: Decimal  # line_total - discount_allocated
    split_applied: Decimal | None = None
    split_amount: Decimal = ZERO


@dataclass(frozen=True)
class SaleCalculationResult:
    items_total: Decimal
    discount_amount: Decimal
    gross_amount: Decimal

    fee_rate: Decimal  # percentual efetivo aplicado (auditoria)
    fee_amount: Decimal  # taxa TOTAL da transação

    split_rate: Decimal
    split_base_used: SplitBase
    split_amount: Decimal

    fee_payer: FeePayer
    fee_amount_charged_to_professional: Decimal  # "taxa_dela"

    cost_provisioned: Decimal
    cost_realized: Decimal

    net_profit: Decimal  # usa cost_realized
    margin: Decimal | None  # net_profit / gross_amount; None se gross=0

    items: list[ItemCalculationResult]


def _find_fee_rule(rules: list[FeeRule], installments: int) -> FeeRule | None:
    for rule in rules:
        if rule.installments_min <= installments <= rule.installments_max:
            return rule
    return None


def _line_totals(items: list[LineItem]) -> list[Decimal]:
    return [money(item.unit_price * item.quantity) for item in items]


def _resolve_cost(item: LineItem) -> Decimal:
    """Soma o custo das sessões não-expiradas do item. session_costs já
    veio filtrado (sem EXPIRED) e já resolvido (COALESCE cost_override,
    item.unit_cost_estimated) por quem monta o LineItem."""
    return money(sum(item.session_costs, ZERO))


def _provisioned_cost(item: LineItem) -> Decimal:
    """Custo estimado no DIA 1 — antes de qualquer sessão acontecer:
    unit_cost_estimated × quantity, sem COALESCE de cost_override (§12.1).
    """
    return money(item.unit_cost_estimated * item.quantity)


def _sum_realized_cost(items: list[LineItem]) -> Decimal:
    return money(sum((_resolve_cost(i) for i in items), ZERO))


def calculate_sale(items: list[LineItem], params: SaleParams) -> SaleCalculationResult:
    if not items:
        raise ValueError("venda sem itens")

    line_totals = _line_totals(items)
    items_total = money(sum(line_totals, ZERO))

    discount = money(params.discount_amount)
    if discount > items_total:
        raise ValueError("desconto não pode exceder o total dos itens")

    gross_amount = money(items_total - discount)

    # Rateio do desconto proporcional a line_total de cada item (§11.5) —
    # allocate() já é largest-remainder, a soma fecha exatamente.
    discount_allocations = (
        allocate(discount, line_totals) if discount > ZERO else [ZERO] * len(items)
    )

    nets_of_discount = [
        money(lt - alloc) for lt, alloc in zip(line_totals, discount_allocations, strict=True)
    ]

    # Taxa: calcula sobre o TOTAL, não por item (backend/ENGENHARIA.md §5).
    rule = _find_fee_rule(params.fee_rules, params.installments)
    fee_rate = rule.fee_percentage if rule else ZERO
    fixed_fee = rule.fixed_fee if rule else ZERO

    # E7: Se antecipa crédito parcelado, adiciona taxa de antecipação
    if (
        params.payment_method == PaymentMethod.CREDIT
        and params.anticipates_all
        and params.anticipation_rate_per_installment is not None
        and params.installments > 0
    ):
        anticipation_fee = params.anticipation_rate_per_installment * Decimal(params.installments)
        fee_rate = fee_rate + anticipation_fee

    fee_amount = money(apply_rate(gross_amount, fee_rate / Decimal(100)) + fixed_fee)

    has_split_override = any(item.split_override is not None for item in items)

    if has_split_override:
        # Rateio item a item com split customizado
        if params.split_base is SplitBase.NET_OF_FEE:
            fee_allocations = (
                allocate(fee_amount, nets_of_discount) if fee_amount > ZERO else [ZERO] * len(items)
            )
        else:
            fee_allocations = [ZERO] * len(items)

        item_results = []
        item_splits = []
        for item, line_total, disc_alloc, net_disc, fee_alloc in zip(
            items, line_totals, discount_allocations, nets_of_discount, fee_allocations, strict=True
        ):
            base_split_item = money(net_disc - fee_alloc)
            item_split_rate = (
                item.split_override
                if item.split_override is not None
                else params.split_clinic_percentage
            )
            item_split_amt = apply_rate(base_split_item, item_split_rate / Decimal(100))
            item_splits.append(item_split_amt)
            item_results.append(
                ItemCalculationResult(
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    line_total=line_total,
                    discount_allocated=disc_alloc,
                    net_of_discount=net_disc,
                    split_applied=item_split_rate,
                    split_amount=item_split_amt,
                )
            )
        split_amount = money(sum(item_splits, ZERO))
        split_rate = params.split_clinic_percentage
    else:
        item_results = [
            ItemCalculationResult(
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=line_total,
                discount_allocated=alloc,
                net_of_discount=net_disc,
                split_applied=params.split_clinic_percentage,
                split_amount=ZERO,
            )
            for item, line_total, alloc, net_disc in zip(
                items, line_totals, discount_allocations, nets_of_discount, strict=True
            )
        ]
        split_rate = params.split_clinic_percentage
        if params.split_base is SplitBase.NET_OF_FEE:
            base_split = money(gross_amount - fee_amount)
        else:
            base_split = gross_amount
        split_amount = apply_rate(base_split, split_rate / Decimal(100))

    if params.fee_payer is FeePayer.CLINIC:
        fee_charged = ZERO
    elif params.fee_payer is FeePayer.SPLIT_PRO_RATA:
        pro_rata_factor = Decimal(1) - (split_rate / Decimal(100))
        fee_charged = money(fee_amount * pro_rata_factor)
    else:  # PROFESSIONAL
        fee_charged = fee_amount

    net_profit = money(
        gross_amount - split_amount - fee_charged - _sum_realized_cost(items)
    )

    cost_provisioned = money(sum((_provisioned_cost(i) for i in items), ZERO))
    cost_realized = _sum_realized_cost(items)
    margin = None
    if gross_amount != ZERO:
        margin = (net_profit / gross_amount).quantize(Decimal("0.0001"))

    return SaleCalculationResult(
        items_total=items_total,
        discount_amount=discount,
        gross_amount=gross_amount,
        fee_rate=fee_rate,
        fee_amount=fee_amount,
        split_rate=split_rate,
        split_base_used=params.split_base,
        split_amount=split_amount,
        fee_payer=params.fee_payer,
        fee_amount_charged_to_professional=fee_charged,
        cost_provisioned=cost_provisioned,
        cost_realized=cost_realized,
        net_profit=net_profit,
        margin=margin,
        items=item_results,
    )


def expected_receipt_date(
    payment_method: PaymentMethod,
    sold_at: date,
    installments: int,
    anticipates: bool = False,
) -> date | None:
    """Lucro não é caixa (MVP v6 TASK-021, invariante I7). PIX/débito/
    dinheiro/transferência: D+0 (mesmo dia). Crédito: D+30 por parcela ou
    D+2 quando antecipação automática estiver ativa (E7).
    """
    if payment_method == PaymentMethod.CREDIT:
        if anticipates:
            return sold_at + timedelta(days=2)
        return sold_at + timedelta(days=30 * installments)
    return sold_at
