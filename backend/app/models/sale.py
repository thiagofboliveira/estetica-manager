"""Sale — a unidade de DINHEIRO (MVP v6 §11, TASK-012).

Princípio (§11.1): Sale é sempre a unidade de dinheiro. O que varia é
quantas sessões ela cobre (SaleItem/Session). Todo valor financeiro vive
aqui — NUNCA em Session (invariante I5).

Snapshot congelado (invariante I3): split_applied, split_base_applied,
fee_payer_applied, fee_applied, fee_amount_applied são copiados de
FinancialSettings/PaymentFeeRule NO ATO DA VENDA e nunca mais relidos da
config atual. Mudar financial_settings depois NUNCA altera net_profit de
vendas passadas — é o que o CheckConstraint abaixo e o listener
before_flush (T-020b) protegem.

cost_provisioned vs cost_realized (§12.1): provisionado = soma estimada
no dia da venda; realizado = recalculado quando sessões mudam de status
(COMPLETED aplica cost_override se houver; EXPIRED libera o custo). Numa
venda avulsa cost_provisioned == cost_realized desde o início porque a
única sessão já nasce COMPLETED seria incomum — na prática o avulso
também provisiona e realiza no fluxo normal de PATCH /sessions.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, Enum, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel
from app.models.financial_settings import FeePayer, PaymentMethod, SplitBase


class SaleType(StrEnum):
    SINGLE = "SINGLE"
    PACKAGE = "PACKAGE"


class SaleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Sale(TenantModel):
    __tablename__ = "sales"
    __table_args__ = (
        # Identidade contábil garantida pelo BANCO (backend/ENGENHARIA.md
        # §4) — sobrevive a bug de aplicação e a correção manual via SQL.
        CheckConstraint(
            "gross_amount = items_total - discount_amount",
            name="ck_sales_gross_coerente",
        ),
        # FK composta (id, professional_id) para sale_items/sessions
        # denormalizarem professional_id sem JOIN na policy de RLS.
        UniqueConstraint("id", "professional_id", name="uq_sales_id_professional"),
    )

    patient_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    type: Mapped[SaleType] = mapped_column(
        Enum(SaleType, name="sale_type", native_enum=False), nullable=False
    )
    sold_at: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus, name="sale_status", native_enum=False),
        nullable=False,
        default=SaleStatus.ACTIVE,
    )

    # Pagamento — da venda inteira, não da sessão.
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method", native_enum=False), nullable=False
    )
    installments: Mapped[int] = mapped_column(nullable=False, default=1)

    # Valores
    items_total: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), default=Decimal("0.00")
    )
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))

    # SNAPSHOT congelado no ato da venda — FROZEN_FIELDS (nunca UPDATE).
    split_applied: Mapped[Decimal] = mapped_column(Numeric(5, 2, asdecimal=True))
    # Valor em R$ do split — split_applied é só o percentual (v7.1,
    # necessário para o ranking de procedimentos ratear por item, §13).
    split_amount_applied: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), default=Decimal("0.00")
    )
    split_base_applied: Mapped[SplitBase] = mapped_column(
        Enum(SplitBase, name="split_base", native_enum=False)
    )
    fee_payer_applied: Mapped[FeePayer] = mapped_column(
        Enum(FeePayer, name="fee_payer", native_enum=False)
    )
    fee_applied: Mapped[Decimal] = mapped_column(Numeric(5, 2, asdecimal=True))
    fee_amount_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    # Taxa que ELA de fato pagou, após aplicar fee_payer — diferente de
    # fee_amount_applied (taxa TOTAL da transação, ignora quem paga).
    fee_amount_charged_applied: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), default=Decimal("0.00")
    )

    # Custo — provisionado no dia 1, realizado recalculado conforme
    # sessões completam/expiram (§12.1). ÚNICA exceção ao congelamento
    # total (I3 permite isso por design).
    cost_provisioned: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    cost_realized: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))

    # Resultados — net_profit usa cost_realized (lucro "vivo" até a
    # última sessão; ver "lucro provisório" no dashboard, invariante I7).
    net_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True))
    margin: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4, asdecimal=True), nullable=True
    )
    expected_receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    # Auditoria da fórmula aplicada — payload bruto do cálculo (ver
    # domain/financial/calculator.py::SaleCalculationResult), para
    # reconstituir "por que esse número" sem depender da config atual.
    snapshot_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Idempotência do POST /sales (T-015a, contrato C-1): mesma chave +
    # mesmo corpo em 24h -> mesma venda. Único por tenant (não global:
    # duas profissionais podem usar a mesma chave por coincidência).
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)
    idempotency_body_hash: Mapped[str | None] = mapped_column(String, nullable=True)
