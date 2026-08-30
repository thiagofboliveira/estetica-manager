"""SaleItem — linha de uma Sale (MVP v6 §11, TASK-013).

Um pacote de "4 limpezas + 2 peelings" tem dois itens; uma venda avulsa
tem um item com quantity=1 — mesmo caminho de código, sem ramificação
(§11.3).

unit_price, unit_cost_estimated e return_interval_applied são congelados
do Procedure no ato da venda (invariante I3) — mudar o procedimento
depois não altera itens de vendas passadas.

discount_allocated é o rateio do discount_amount da Sale proporcional a
(unit_price × quantity) de cada item (§11.5) — calculado via
core/money.py::allocate() (largest remainder), nunca "o último absorve".
Persistido aqui porque o ranking de procedimentos (§13, fora de escopo
desta task) depende de "quanto cada procedimento realmente rendeu".
"""

from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class SaleItem(TenantModel):
    __tablename__ = "sale_items"
    __table_args__ = (
        # FK composta contra (sales.id, sales.professional_id): garante
        # que um sale_item nunca aponta para uma sale de outro tenant,
        # mesmo que professional_id seja carimbado por engano errado
        # (defesa em profundidade, backend/ENGENHARIA.md §1).
        ForeignKeyConstraint(
            ["sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_sale_items_sale",
            ondelete="RESTRICT",
        ),
        # Necessário para sessions referenciar (sale_item_id,
        # professional_id) via FK composta — mesmo padrão de sales.
        UniqueConstraint("id", "professional_id", name="uq_sale_items_id_professional"),
    )

    sale_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    procedure_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("procedures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Congelados do Procedure no ato da venda.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    unit_cost_estimated: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    return_interval_applied: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Rateio do desconto da venda (§11.5) — soma dos itens fecha
    # exatamente com sales.discount_amount.
    discount_allocated: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), default=Decimal("0.00")
    )
