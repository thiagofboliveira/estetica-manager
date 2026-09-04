"""FinancialSettings — configuração financeira do tenant (MVP v6 §8, TASK-007).

Singleton por professional_id: uma linha por profissional, criada com
defaults de mercado (§8.1) na primeira leitura se ainda não existir —
nunca copiada de outra conta.

split_base (E2) e fee_payer (E1) alimentam a fórmula do motor de lucro
(§12) e são também congelados no snapshot de cada Sale (invariante I3) —
esta tabela é só a configuração VIGENTE, mudá-la não deve alterar vendas
passadas.
"""

from datetime import time
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, Numeric, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


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


class FinancialSettings(TenantModel):
    __tablename__ = "financial_settings"
    __table_args__ = (
        # Singleton por tenant — uma config vigente por professional_id.
        UniqueConstraint("professional_id", name="uq_financial_settings_professional"),
    )

    split_clinic_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2, asdecimal=True), nullable=False, default=Decimal("0.00")
    )
    split_base: Mapped[SplitBase] = mapped_column(
        Enum(SplitBase, name="split_base", native_enum=False),
        nullable=False,
        default=SplitBase.GROSS,
    )
    fee_payer: Mapped[FeePayer] = mapped_column(
        Enum(FeePayer, name="fee_payer", native_enum=False),
        nullable=False,
        default=FeePayer.PROFESSIONAL,
    )
    pix_fee_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2, asdecimal=True), nullable=False, default=Decimal("0.00")
    )
    debit_card_fee_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2, asdecimal=True), nullable=False, default=Decimal("1.99")
    )
    default_payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method", native_enum=False),
        nullable=False,
        default=PaymentMethod.PIX,
    )
    # E7 — Antecipação de Recebíveis (P1)
    anticipates_all: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    anticipation_rate_per_installment: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2, asdecimal=True), nullable=True
    )
    # Épico A — "Modo Ocupado" (roadmap 2026-09-02): janela de trabalho
    # usada para calcular horários livres a sugerir no WhatsApp.
    work_start_time: Mapped[time] = mapped_column(
        Time, nullable=False, default=time(8, 0)
    )
    work_end_time: Mapped[time] = mapped_column(
        Time, nullable=False, default=time(18, 0)
    )
    slot_duration_minutes: Mapped[int] = mapped_column(nullable=False, default=30)
    buffer_minutes: Mapped[int] = mapped_column(nullable=False, default=15)
