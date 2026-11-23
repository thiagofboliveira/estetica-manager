"""AIUsage — contador mensal de textos gerados por IA (AI-01).

Existe só para impor o teto de custo por profissional. Não guarda o texto
gerado, nem dado de paciente: apenas quantos rascunhos foram gerados no mês.
"""

from datetime import date

from sqlalchemy import Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class AIUsage(TenantModel):
    __tablename__ = "ai_usage"
    __table_args__ = (
        UniqueConstraint("professional_id", "period_month", name="uq_ai_usage_month"),
    )

    # Sempre o primeiro dia do mês, no fuso da profissional (I4).
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    drafts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
