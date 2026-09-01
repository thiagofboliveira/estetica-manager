"""Projeção de Recebíveis Futuros (MVP v6 P1, EPIC-S3-03).

PURO: sem SQLAlchemy, sem FastAPI, sem I/O.
Calcula o cronograma projetado de repasses de vendas a prazo (cartão de crédito parcelado)
mês a mês ao longo de uma janela futura (ex: 6 a 12 meses).
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.core.money import ZERO, allocate, money


@dataclass(frozen=True)
class SaleReceivableInput:
    sale_id: str
    sold_at: date
    payment_method: str  # "CREDIT", "PIX", etc.
    installments: int
    net_received_amount: Decimal  # Valor líquido que a profissional recebe após taxas da adquirente
    is_anticipated: bool = False


@dataclass(frozen=True)
class MonthlyReceivableProjection:
    year_month: str  # "2026-09"
    total_amount: Decimal
    installment_count: int


def project_monthly_receivables(
    sales: list[SaleReceivableInput],
    reference_date: date,
    months_ahead: int = 12,
) -> list[MonthlyReceivableProjection]:
    """Projeta os recebíveis futuros agrupados por mês (YYYY-MM).

    Para vendas não-antecipadas em cartão de crédito:
    - 1x cai em D+30 (mês seguinte).
    - 2x cai em D+30 e D+60.
    - k parcelas caem em sold_at + 30*k dias.

    Vendas em PIX, dinheiro ou antecipadas caem no próprio mês da venda (ou D+0/D+2).
    """
    buckets: dict[str, Decimal] = defaultdict(lambda: ZERO)
    counts: dict[str, int] = defaultdict(int)

    for s in sales:
        if s.net_received_amount <= ZERO:
            continue

        if s.payment_method != "CREDIT" or s.is_anticipated or s.installments <= 1:
            # Recebimento imediato / à vista / antecipado
            if s.is_anticipated:
                receipt_date = s.sold_at + timedelta(days=2)
            elif s.payment_method == "CREDIT" and s.installments == 1:
                receipt_date = s.sold_at + timedelta(days=30)
            else:
                receipt_date = s.sold_at

            ym = receipt_date.strftime("%Y-%m")
            buckets[ym] += s.net_received_amount
            counts[ym] += 1
        else:
            # Parcelado sem antecipação: divide em N parcelas de 30 em 30 dias
            num_inst = max(1, s.installments)
            # Divide com maior resto para fechar centavos exatos
            weights = [1] * num_inst
            inst_amounts = allocate(s.net_received_amount, weights)

            for k, inst_amt in enumerate(inst_amounts, start=1):
                inst_date = s.sold_at + timedelta(days=30 * k)
                ym = inst_date.strftime("%Y-%m")
                buckets[ym] += inst_amt
                counts[ym] += 1

    # Monta a lista sequencial a partir do mês atual até months_ahead
    result: list[MonthlyReceivableProjection] = []
    curr_year = reference_date.year
    curr_month = reference_date.month

    for _ in range(months_ahead):
        ym_key = f"{curr_year:04d}-{curr_month:02d}"
        result.append(
            MonthlyReceivableProjection(
                year_month=ym_key,
                total_amount=money(buckets[ym_key]),
                installment_count=counts[ym_key],
            )
        )
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1

    return result
