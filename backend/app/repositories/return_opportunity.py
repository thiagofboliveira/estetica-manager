"""ReturnOpportunityRepository (MVP v7.1 §14, TASK-025/028/029)."""

from uuid import UUID

from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
)
from app.models.patient import Patient
from app.models.procedure import Procedure
from app.models.return_opportunity import ReturnOpportunity
from app.repositories.base import TenantRepository

# Usado por list_open_or_contacted_for_patient_and_procedure() (fechamento
# automático na venda, T-028, RetentionService.close_open_opportunities).
# Inclui BOOKED e DECLINED porque ambos são status não-CLOSED válidos: uma
# oportunidade marcada BOOKED (paciente topou voltar) ainda precisa ser
# encontrada e fechada quando a venda correspondente de fato acontecer —
# excluí-la aqui (bug corrigido nesta revisão final) deixava a oportunidade
# presa em BOOKED para sempre, sem resolved_by_sale_id, bloqueando o índice
# parcial único (uq_return_opportunities_source_sale_item_active) de
# permitir uma nova oportunidade futura para o mesmo item de venda.
_ACTIVE_FOR_CLOSING = (
    ReturnOpportunityStatus.OPEN,
    ReturnOpportunityStatus.CONTACTED,
    ReturnOpportunityStatus.NO_RESPONSE,
    ReturnOpportunityStatus.BOOKED,
    ReturnOpportunityStatus.DECLINED,
)

# Usado por list_non_terminal_with_details() (tela de reativação,
# GET /retention/opportunities). Deliberadamente MENOR que
# _ACTIVE_FOR_CLOSING acima: BOOKED/DECLINED já têm uma resposta da
# paciente e não devem poluir a lista de "quem ligar hoje" — ficam
# aguardando apenas o fechamento automático pela venda, não uma nova ação
# da profissional na tela.
_VISIBLE_ON_SCREEN = (
    ReturnOpportunityStatus.OPEN,
    ReturnOpportunityStatus.CONTACTED,
    ReturnOpportunityStatus.NO_RESPONSE,
)


class ReturnOpportunityRepository(TenantRepository[ReturnOpportunity]):
    model = ReturnOpportunity

    def find_active_for_sale_item(
        self, sale_item_id: UUID
    ) -> ReturnOpportunity | None:
        """Índice parcial único garante no máximo 1 linha não-CLOSED por
        item — usado para não duplicar oportunidade ao reprocessar
        exaustão (RetentionService.check_and_create_opportunity)."""
        stmt = self._scoped().where(
            ReturnOpportunity.source_sale_item_id == sale_item_id,
            ReturnOpportunity.status != ReturnOpportunityStatus.CLOSED,
        )
        return self._session.scalars(stmt).one_or_none()

    def list_open_or_contacted_for_patient_and_procedure(
        self, patient_id: UUID, procedure_id: UUID
    ) -> list[ReturnOpportunity]:
        """Base do fechamento automático na venda (T-028) — inclui
        NO_RESPONSE porque uma paciente que não respondeu ainda tem a
        oportunidade "em aberto" do ponto de vista de negócio."""
        stmt = self._scoped().where(
            ReturnOpportunity.patient_id == patient_id,
            ReturnOpportunity.procedure_id == procedure_id,
            ReturnOpportunity.status.in_(_ACTIVE_FOR_CLOSING),
        )
        return list(self._session.scalars(stmt))

    def list_non_terminal_with_details(
        self,
    ) -> list[tuple[ReturnOpportunity, Patient, Procedure]]:
        """Junta patient/procedure para a tela de reativação (T-029/030)
        — evita N+1 queries do lado do service."""
        stmt = (
            self._scoped()
            .where(ReturnOpportunity.status.in_(_VISIBLE_ON_SCREEN))
            .join(Patient, Patient.id == ReturnOpportunity.patient_id)
            .join(Procedure, Procedure.id == ReturnOpportunity.procedure_id)
            .add_columns(Patient, Procedure)
        )
        return [
            (opp, patient, procedure)
            for opp, patient, procedure in self._session.execute(stmt).all()
        ]
