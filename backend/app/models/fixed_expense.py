"""FixedExpense — despesa fixa recorrente do tenant (MVP v7.1 §12.5, T-021a).

Nasceu da entrevista com a cliente zero: ela não tem split percentual de
clínica, paga aluguel fixo de sala + água/luz/lixo biológico/taxa anual
de vigilância sanitária. É uma categoria ortogonal ao motor de lucro por
venda (EPIC-08) — existe mesmo em um mês sem nenhuma venda.

Vigência (active_from/active_to), não snapshot por venda: se o valor
mudar, fecha o registro antigo e abre um novo (mesmo princípio de
ConfigVersion, aplicado de forma mais simples porque não precisa de
congelamento por transação).

periodicity (MONTHLY | YEARLY) existe porque a taxa de vigilância
sanitária é anual, não mensal — sem isso o "Lucro real do mês" (T-022)
ficaria otimista nos 11 meses sem a cobrança. amount é sempre o valor do
CICLO declarado (ex: R$1.200/ano), nunca pré-rateado pelo usuário; o
rateio (÷12 para YEARLY) acontece no cálculo do dashboard, não aqui.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class ExpensePeriodicity(StrEnum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class FixedExpense(TenantModel):
    __tablename__ = "fixed_expenses"

    label: Mapped[str] = mapped_column(String, nullable=False)
    # Texto livre de propósito — só um caso real (aluguel) existia na
    # entrevista; inventar um enum fechado seria projetar para hipótese.
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True), nullable=False)
    periodicity: Mapped[ExpensePeriodicity] = mapped_column(
        Enum(ExpensePeriodicity, name="expense_periodicity", native_enum=False),
        nullable=False,
        default=ExpensePeriodicity.MONTHLY,
    )
    active_from: Mapped[date] = mapped_column(Date, nullable=False)
    # NULL = ainda vigente. "Excluir" fecha active_to=hoje, nunca hard delete.
    active_to: Mapped[date | None] = mapped_column(Date, nullable=True)
