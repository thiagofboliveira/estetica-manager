from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class LoyaltyTransactionType(StrEnum):
    EARNED = "EARNED"          # Pontos ganhos por compra de procedimento/sessão
    BONUS = "BONUS"            # Bônus por indicação de amiga ("Traga uma Amiga") ou campanha
    REDEEMED = "REDEEMED"      # Pontos resgatados / convertidos em desconto
    ADJUSTMENT = "ADJUSTMENT"  # Ajuste manual ou cortesia pela profissional


class LoyaltyTransaction(TenantModel):
    """Extrato e histórico contábil de pontos de fidelidade do paciente."""

    __tablename__ = "loyalty_transactions"

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sale_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=LoyaltyTransactionType.EARNED
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
