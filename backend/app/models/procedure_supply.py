"""ProcedureSupply — Ficha técnica: insumos consumidos por procedimento."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel


class ProcedureSupply(TenantModel):
    __tablename__ = "procedure_supplies"
    __table_args__ = (
        UniqueConstraint("procedure_id", "supply_id", name="uq_procedure_supplies_procedure_supply"),
    )

    procedure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("procedures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supply_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("supplies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False, default=Decimal("1.00")
    )

    procedure = relationship("Procedure", back_populates="supplies")
    supply = relationship("Supply", lazy="joined")
