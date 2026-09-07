"""OpenVial — Rastreamento inteligente de frascos e insumos perecíveis (US-03).

Controla frascos de Toxina Botulínica e outros insumos de alto custo abertos
na geladeira (validade padrão de 30 dias após reconstituição) para evitar desperdício.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel


class VialStatus(StrEnum):
    OPEN = "OPEN"
    FINISHED = "FINISHED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"


class OpenVial(TenantModel):
    __tablename__ = "open_vials"

    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    procedure_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("procedures.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supply_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("supplies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    medication_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Toxina Botulínica",
    )
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_units: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("100.00")
    )
    used_units: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    unit_measure: Mapped[str] = mapped_column(
        String(20), nullable=False, default="U"
    )
    cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    opened_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=30),
        nullable=False,
    )
    status: Mapped[VialStatus] = mapped_column(
        Enum(VialStatus, name="vial_status", native_enum=False),
        default=VialStatus.OPEN,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    procedure = relationship("Procedure", foreign_keys=[procedure_id])

    @property
    def remaining_units(self) -> Decimal:
        return max(Decimal("0.00"), self.total_units - self.used_units)
