"""Procedure. type distingue serviço (tem janela de retorno) de produto
revendido (não tem) — sem isso, revenda de dermocosmético seria forçada
a virar um "procedimento" falso, poluindo o ranking (MVP v6 §9).

price e estimated_cost aqui são DEFAULTS de UI, nunca fonte de verdade:
o valor aplicado numa venda é congelado no snapshot (invariante I3) e
mudar o procedimento depois não altera vendas passadas.
"""

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class ProcedureType(StrEnum):
    SERVICE = "SERVICE"
    PRODUCT = "PRODUCT"


class Procedure(TenantModel):
    __tablename__ = "procedures"

    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[ProcedureType] = mapped_column(
        Enum(ProcedureType, name="procedure_type", native_enum=False),
        default=ProcedureType.SERVICE,
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    # Nulo para PRODUCT — produto revendido não tem janela de retorno.
    return_interval_days: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
