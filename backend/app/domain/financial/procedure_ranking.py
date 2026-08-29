"""Ranking de procedimentos (MVP v6 §13, TASK-024).

PURO: sem SQLAlchemy, sem FastAPI (backend/ENGENHARIA.md §5).

⚠️ Só é confiável se E4 (parcelamento) e E5 (custo variável) estiverem
resolvidos — com taxa de parcelamento e custo ignorados, o ranking fica
enviesado a favor de procedimentos caros/parcelados, o que é dano ativo
(induz a profissional a errar o mix).

Fórmula de "lucro por item" (v7.1, decisão de implementação registrada
no MVP §13): split_amount e fee_charged da venda são rateados entre os
itens na MESMA proporção usada para discount_allocated (unit_price ×
quantity, via allocate() — largest remainder). Base: **item**, não
venda nem sessão (§13.1) — agrupa por procedure_id.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.core.money import ZERO, allocate, money


@dataclass(frozen=True)
class ItemForRanking:
    """Recorte de SaleItem + o gross/split/fee da Sale que ele pertence,
    suficiente para o rateio — não os models inteiros."""

    procedure_id: UUID
    procedure_name: str
    unit_price: Decimal
    quantity: int
    unit_cost_estimated: Decimal
    discount_allocated: Decimal
    # Da Sale pai — mesmos para todos os itens da mesma venda, repetidos
    # aqui para o domínio não precisar saber o que é uma "venda".
    sale_split_amount: Decimal
    sale_fee_charged: Decimal
    sale_line_totals_sum: Decimal  # Σ (unit_price × quantity) de TODOS os itens da venda


@dataclass(frozen=True)
class ProcedureRankingRow:
    procedure_id: UUID
    procedure_name: str
    gross_revenue: Decimal
    net_profit: Decimal
    margin: Decimal | None


def _line_total(item: ItemForRanking) -> Decimal:
    return money(item.unit_price * item.quantity)


def build_procedure_ranking(items: list[ItemForRanking]) -> list[ProcedureRankingRow]:
    # Agrupa por venda primeiro (mesma sale_split_amount/sale_fee_charged
    # e sale_line_totals_sum) para ratear split/taxa dentro de cada venda
    # com allocate() — não dá para ratear itens de vendas DIFERENTES
    # juntos, o rateio é sempre dentro do total de uma venda.
    by_sale_key: dict[tuple[Decimal, Decimal, Decimal], list[ItemForRanking]] = {}
    for item in items:
        key = (item.sale_split_amount, item.sale_fee_charged, item.sale_line_totals_sum)
        by_sale_key.setdefault(key, []).append(item)

    accumulated: dict[UUID, dict[str, Decimal | str]] = {}

    for (split_amount, fee_charged, _line_totals_sum), sale_items in by_sale_key.items():
        line_totals = [_line_total(i) for i in sale_items]
        split_allocations = (
            allocate(split_amount, line_totals) if split_amount > ZERO else [ZERO] * len(sale_items)
        )
        fee_allocations = (
            allocate(fee_charged, line_totals) if fee_charged > ZERO else [ZERO] * len(sale_items)
        )

        for item, line_total, split_alloc, fee_alloc in zip(
            sale_items, line_totals, split_allocations, fee_allocations, strict=True
        ):
            net_of_discount = money(line_total - item.discount_allocated)
            item_cost = money(item.unit_cost_estimated * item.quantity)
            item_profit = money(net_of_discount - split_alloc - fee_alloc - item_cost)

            acc = accumulated.setdefault(
                item.procedure_id,
                {"name": item.procedure_name, "revenue": ZERO, "profit": ZERO},
            )
            acc["revenue"] = money(acc["revenue"] + net_of_discount)
            acc["profit"] = money(acc["profit"] + item_profit)

    rows = [
        ProcedureRankingRow(
            procedure_id=proc_id,
            procedure_name=str(acc["name"]),
            gross_revenue=acc["revenue"],
            net_profit=acc["profit"],
            margin=(acc["profit"] / acc["revenue"]) if acc["revenue"] != ZERO else None,
        )
        for proc_id, acc in accumulated.items()
    ]
    return sorted(rows, key=lambda r: r.gross_revenue, reverse=True)
