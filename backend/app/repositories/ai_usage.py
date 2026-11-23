from datetime import date
from typing import Literal

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from app.models.ai_usage import AIUsage
from app.repositories.base import TenantRepository

Counter = Literal["drafts_count", "fallbacks_count", "sent_count", "edited_count"]
COUNTERS: tuple[str, ...] = (
    "drafts_count",
    "fallbacks_count",
    "sent_count",
    "edited_count",
)


class AIUsageRepository(TenantRepository[AIUsage]):
    model = AIUsage

    def get_month(self, period_month: date) -> AIUsage | None:
        return self._session.scalars(
            self._scoped().where(AIUsage.period_month == period_month)
        ).one_or_none()

    def count_for(self, period_month: date) -> int:
        row = self.get_month(period_month)
        return row.drafts_count if row else 0

    def increment(self, period_month: date, counter: Counter = "drafts_count") -> int:
        """Soma 1 ao contador do mês e devolve o novo valor. Upsert atômico:
        dois pedidos simultâneos não perdem contagem."""
        if counter not in COUNTERS:
            raise ValueError(f"contador desconhecido: {counter}")
        self._session.execute(
            insert(AIUsage)
            .values(
                professional_id=self._professional_id,
                period_month=period_month,
                drafts_count=0,
            )
            .on_conflict_do_nothing(constraint="uq_ai_usage_month")
        )
        column = getattr(AIUsage, counter)
        self._session.execute(
            update(AIUsage)
            .where(
                AIUsage.professional_id == self._professional_id,
                AIUsage.period_month == period_month,
            )
            .values({counter: column + 1})
        )
        self._session.expire_all()
        row = self.get_month(period_month)
        return getattr(row, counter) if row else 0
