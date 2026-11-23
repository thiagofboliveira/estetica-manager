from datetime import date

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from app.models.ai_usage import AIUsage
from app.repositories.base import TenantRepository


class AIUsageRepository(TenantRepository[AIUsage]):
    model = AIUsage

    def count_for(self, period_month: date) -> int:
        row = self._session.scalars(
            self._scoped().where(AIUsage.period_month == period_month)
        ).one_or_none()
        return row.drafts_count if row else 0

    def increment(self, period_month: date) -> int:
        """Soma 1 ao mês e devolve o total. Upsert atômico: dois pedidos
        simultâneos não perdem contagem."""
        self._session.execute(
            insert(AIUsage)
            .values(
                professional_id=self._professional_id,
                period_month=period_month,
                drafts_count=0,
            )
            .on_conflict_do_nothing(constraint="uq_ai_usage_month")
        )
        self._session.execute(
            update(AIUsage)
            .where(
                AIUsage.professional_id == self._professional_id,
                AIUsage.period_month == period_month,
            )
            .values(drafts_count=AIUsage.drafts_count + 1)
        )
        return self.count_for(period_month)
