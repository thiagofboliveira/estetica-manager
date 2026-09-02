"""SaleAudit — trilha de correção de venda (MVP v6 §27, TASK-017).

Filosofia deliberada: NUNCA UPDATE numa Sale já persistida (ver
FROZEN_FIELDS em app/models/listeners.py — "para corrigir, estorne e
refaça"). Corrigir uma venda errada significa: (1) marcar a venda
original como REFUNDED, (2) criar uma venda NOVA com os dados corretos,
(3) registrar aqui o vínculo entre as duas + o motivo. O histórico
contábil da venda original nunca é reescrito — apenas encerrado.

Limitação conhecida (ausência de T-020a): a venda de substituição usa a
config financeira ATUAL (financial_settings/payment_fee_rules vigentes),
não a config do momento da venda original — o sistema não tem
versionamento por data de vigência dessas configs. Se elas não mudaram
entre as duas vendas, o resultado é idêntico ao que seria com a config
"correta"; se mudaram, a correção reflete a política vigente hoje, não a
de quando a venda original foi feita.
"""

from datetime import datetime

from sqlalchemy import ForeignKeyConstraint, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class SaleAudit(TenantModel):
    __tablename__ = "sale_audit"
    __table_args__ = (
        ForeignKeyConstraint(
            ["original_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_sale_audit_original_sale",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["replacement_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_sale_audit_replacement_sale",
            ondelete="RESTRICT",
        ),
    )

    original_sale_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    replacement_sale_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String, nullable=False)
    # Instante técnico (TIMESTAMPTZ, UTC) — diferente de Sale.sold_at,
    # que é uma DATA de negócio e por isso usa o fuso da profissional
    # (invariante I4). corrected_at não precisa de conversão de fuso:
    # não é usado para agrupar por dia, só para ordenar/auditar.
    corrected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
