"""AttributionService — Orquestra o cálculo de ROI e Receita Recuperada (EPIC-S2-01, TASK-BACK-S2-03)."""

from datetime import date
from decimal import Decimal

from app.core.tz import today_in_timezone
from app.domain.financial.attribution import (
    AttributedCandidate,
    AttributionResult,
    calculate_attributed_revenue,
)
from app.domain.financial.period import resolve_period
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository

DEFAULT_SUBSCRIPTION_FEE = Decimal("97.00")


class AttributionService:
    def __init__(
        self,
        opportunity_repo: ReturnOpportunityRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._opportunity_repo = opportunity_repo
        self._professional_repo = professional_repo

    def get_roi(
        self,
        *,
        filter_name: str = "this_month",
        custom_from: date | None = None,
        custom_to: date | None = None,
        subscription_fee: Decimal = DEFAULT_SUBSCRIPTION_FEE,
    ) -> tuple[AttributionResult, str, date, date, bool]:
        professional = self._professional_repo.get_current()
        today = today_in_timezone(professional.timezone)

        period = resolve_period(
            filter_name=filter_name,
            today=today,
            custom_from=custom_from,
            custom_to=custom_to,
        )

        pairs = self._opportunity_repo.list_attributed(
            date_from=period.date_from,
            date_to=period.date_to,
        )

        candidates = [
            AttributedCandidate(
                opportunity_id=opp.id,
                patient_id=opp.patient_id,
                due_date=opp.due_date,
                contacted_at=opp.contacted_at,
                resolved_by_sale_id=opp.resolved_by_sale_id,
                sale_sold_at=sale.sold_at,
                sale_net_profit=sale.net_profit,
            )
            for opp, sale in pairs
        ]

        result = calculate_attributed_revenue(
            candidates=candidates,
            subscription_fee=subscription_fee,
        )

        # Se a data de hoje estiver próxima da data final ou no meio do período,
        # a janela de 21 dias pode cortar o período corrente.
        is_estimated = filter_name in ("this_month", "custom")

        return result, period.kind.value, period.date_from, period.date_to, is_estimated
