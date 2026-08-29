"""PaymentFeeRule — taxas de adquirência por faixa de parcelas (MVP v6 §8,
TASK-008).

Faixas, não uma linha por parcela: à vista ~3,2%, 2-6x ~9-11%, 7-12x
~13-16% (mercado BR). Consultado por (payment_method, installments) — o
motor de lucro (domain/financial) busca a linha cujo intervalo
[installments_min, installments_max] contém o número de parcelas da
venda.

Populado via seed de defaults de mercado na criação da conta (§8.1) —
NUNCA copiado de outra conta.
"""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel
from app.models.financial_settings import PaymentMethod


class PaymentFeeRule(TenantModel):
    __tablename__ = "payment_fee_rules"
    __table_args__ = (
        CheckConstraint(
            "installments_min <= installments_max",
            name="ck_payment_fee_rules_min_le_max",
        ),
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        # native_enum=False + mesmo name do enum já criado em
        # financial_settings — reaproveita o mesmo tipo no banco.
        Enum(PaymentMethod, name="payment_method", native_enum=False),
        nullable=False,
    )
    installments_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    installments_max: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fee_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2, asdecimal=True), nullable=False, default=Decimal("0.00")
    )
    fixed_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00")
    )
