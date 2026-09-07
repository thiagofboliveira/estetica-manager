"""Supply e SupplyMovement — Gestão genérica e completa de insumos clínicos e estoque.

Atende todas as famílias de insumos estéticos:
- Injetáveis & Fracionados (Toxina, Bioestimuladores, Enzimas)
- Preenchedores (Ácido Hialurônico)
- Fios de Sustentação (PDO)
- Anestésicos (Tópicos, Injetáveis)
- Consumíveis & Descartáveis (Agulhas, cânulas, luvas, gaze)
- Outros insumos
"""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel


class SupplyCategory(StrEnum):
    INJECTABLE = "INJECTABLE"      # Toxinas, Bioestimuladores, Enzimas
    FILLER = "FILLER"              # Ácido Hialurônico (seringas)
    THREAD = "THREAD"              # Fios de PDO / sustentação
    ANESTHETIC = "ANESTHETIC"      # Pomadas e ampolas anestésicas
    CONSUMABLE = "CONSUMABLE"      # Agulhas, cânulas, luvas, gazes
    OTHER = "OTHER"                # Outros materiais


class MovementType(StrEnum):
    ENTRY = "ENTRY"                # Compra / Entrada de estoque
    EXIT = "EXIT"                  # Uso em atendimento / Saída avulsa
    ADJUSTMENT = "ADJUSTMENT"      # Balanço / Correção manual de inventário
    LOSS = "LOSS"                  # Perda / Quebra / Vencimento


class Supply(TenantModel):
    __tablename__ = "supplies"

    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[SupplyCategory] = mapped_column(
        Enum(SupplyCategory, name="supply_category", native_enum=False),
        default=SupplyCategory.CONSUMABLE,
        nullable=False,
        index=True,
    )
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_measure: Mapped[str] = mapped_column(String(30), nullable=False, default="UN")
    current_stock: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    min_stock_alert: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    movements = relationship(
        "SupplyMovement",
        back_populates="supply",
        cascade="all, delete-orphan",
        order_by="desc(SupplyMovement.created_at)",
    )

    @property
    def is_low_stock(self) -> bool:
        if self.min_stock_alert is None:
            return False
        return self.current_stock <= self.min_stock_alert


class SupplyMovement(TenantModel):
    __tablename__ = "supply_movements"

    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supply_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("supplies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, name="supply_movement_type", native_enum=False),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supply = relationship("Supply", back_populates="movements")
