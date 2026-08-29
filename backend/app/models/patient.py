"""Patient — dado sensível (LGPD Art. 5º, II). Ver ../../ENGENHARIA.md.

Três estados de exclusão (MVP v6 §10): is_active=False arquiva
(reversível); anonymized_at marca exclusão irreversível de identificação
preservando o histórico financeiro (concilia Art. 18 VI com Art. 16 II).
Hard delete real só por processo administrativo, fora do produto.
"""

from datetime import date, datetime

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class Patient(TenantModel):
    __tablename__ = "patients"

    name: Mapped[str] = mapped_column(nullable=False)
    # E.164 normalizado (+5511987654321) — nunca monte "55{ddd}{phone}" na
    # hora de gerar o link wa.me; normalize uma vez, na gravação.
    phone: Mapped[str | None] = mapped_column(nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(nullable=True)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)

    consent_whatsapp: Mapped[bool] = mapped_column(default=False, nullable=False)
    consent_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    opted_out_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    anonymized_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
