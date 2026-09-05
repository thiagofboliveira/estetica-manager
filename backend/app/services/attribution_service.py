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
from app.repositories.session import SessionRepository
from app.services.financial_settings_service import FinancialSettingsService


class AttributionService:
    def __init__(
        self,
        opportunity_repo: ReturnOpportunityRepository,
        professional_repo: ProfessionalRepository,
        financial_settings_service: FinancialSettingsService,
        session_repo: SessionRepository | None = None,
    ) -> None:
        self._opportunity_repo = opportunity_repo
        self._professional_repo = professional_repo
        self._financial_settings = financial_settings_service
        # Opcional por retrocompatibilidade com quem já instanciava este
        # service (ex.: testes unitários existentes) — sem ele, G-11
        # simplesmente não conta no-show evitado (0), não quebra o ROI.
        self._sessions = session_repo

    def get_roi(
        self,
        *,
        filter_name: str = "this_month",
        custom_from: date | None = None,
        custom_to: date | None = None,
        subscription_fee: Decimal | None = None,
    ) -> tuple[AttributionResult, str, date, date, bool]:
        """G-09: subscription_fee vem da configuração real do tenant
        (financial_settings.subscription_fee), não de uma constante
        hardcoded — o ROI exibido dividia por um valor fixo que podia
        divergir do preço real cobrado (I7). Parâmetro explícito segue
        aceito para simulação/teste, mas o caminho normal (None) sempre
        lê a config."""
        if subscription_fee is None:
            subscription_fee = self._financial_settings.get_or_create_default().subscription_fee

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

        no_show_session_values: list[Decimal] = []
        if self._sessions is not None:
            no_show_session_values = [
                unit_price
                for _session, unit_price in self._sessions.list_no_show_avoided_in_period(
                    period.date_from, period.date_to, professional.timezone
                )
            ]

        result = calculate_attributed_revenue(
            candidates=candidates,
            subscription_fee=subscription_fee,
            no_show_avoided_session_values=no_show_session_values,
        )

        # Se a data de hoje estiver próxima da data final ou no meio do período,
        # a janela de 21 dias pode cortar o período corrente.
        is_estimated = filter_name in ("this_month", "custom")

        return result, period.kind.value, period.date_from, period.date_to, is_estimated
