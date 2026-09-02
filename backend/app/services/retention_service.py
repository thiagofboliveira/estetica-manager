"""RetentionService — orquestra a criação (T-025/026/027) e o
fechamento (T-028) de return_opportunities.

Camada de orquestração (backend/ENGENHARIA.md §5): consulta sessions
reais, chama o domínio puro (window.calculate_due_date) e persiste. O
CÁLCULO da data em si vive em domain/ — testável sem banco.
"""

from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
    validate_transition,
)
from app.domain.retention.window import calculate_due_date
from app.domain.sales.session_state_machine import SessionStatus
from app.models.return_opportunity import ReturnOpportunity
from app.models.sale_item import SaleItem
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.session import SessionRepository

_NON_EXHAUSTING_STATUSES = (
    SessionStatus.PENDING,
    SessionStatus.SCHEDULED,
    SessionStatus.CONFIRMED,
)


class RetentionService:
    def __init__(
        self,
        opportunity_repo: ReturnOpportunityRepository,
        session_repo: SessionRepository,
    ) -> None:
        self._opportunities = opportunity_repo
        self._sessions = session_repo

    def check_and_create_opportunity(
        self,
        *,
        sale_item: SaleItem,
        patient_id: UUID,
        professional_timezone: str,
    ) -> ReturnOpportunity | None:
        """Chamado sempre que uma sessão do item muda de status (T-016).
        Cria a oportunidade apenas se: (1) o procedimento tem intervalo
        de retorno (produtos não têm — §9), (2) o item esgotou (nenhuma
        sessão PENDING/SCHEDULED/CONFIRMED restante), (3) existe ao
        menos uma sessão COMPLETED, (4) não existe já uma oportunidade
        ATIVA para este item (índice parcial único garante isso no
        banco; checar aqui evita round-trip de erro de constraint)."""
        if sale_item.return_interval_applied is None:
            return None

        if self._opportunities.find_active_for_sale_item(sale_item.id) is not None:
            return None

        sessions = self._sessions.list_for_sale_item(sale_item.id)
        if any(s.status in _NON_EXHAUSTING_STATUSES for s in sessions):
            return None

        completed = [s for s in sessions if s.status == SessionStatus.COMPLETED]
        if not completed:
            return None

        last_completed_at = max(s.completed_at for s in completed)
        due_date = calculate_due_date(
            last_completed_at.astimezone(ZoneInfo(professional_timezone)).date(),
            sale_item.return_interval_applied,
        )

        opportunity = ReturnOpportunity(
            patient_id=patient_id,
            procedure_id=sale_item.procedure_id,
            source_sale_item_id=sale_item.id,
            due_date=due_date,
            potential_value=sale_item.unit_price * sale_item.quantity,
            status=ReturnOpportunityStatus.OPEN,
        )
        return self._opportunities.add(opportunity)

    def close_open_opportunities(
        self,
        *,
        patient_id: UUID,
        procedure_id: UUID,
        resolved_by_sale_id: UUID,
    ) -> None:
        """Chamado por SaleService.create() (T-028) na mesma transação da
        nova venda — fecha toda oportunidade não-terminal do mesmo par
        (paciente, procedimento), atribuindo a venda que a resolveu."""
        opportunities = (
            self._opportunities.list_open_or_contacted_for_patient_and_procedure(
                patient_id, procedure_id
            )
        )
        for opportunity in opportunities:
            validate_transition(opportunity.status, ReturnOpportunityStatus.CLOSED)
            opportunity.status = ReturnOpportunityStatus.CLOSED
            opportunity.resolved_by_sale_id = resolved_by_sale_id
        self._opportunities.flush()
