from uuid import UUID

from app.domain.retention.enums import ReturnOpportunityStatus
from app.models.return_opportunity import ReturnOpportunity
from app.repositories.base import TenantRepository


class ReturnOpportunityRepository(TenantRepository[ReturnOpportunity]):
    model = ReturnOpportunity

    def get_by_id(self, opp_id: UUID) -> ReturnOpportunity | None:
        stmt = self._scoped().where(ReturnOpportunity.id == opp_id)
        return self._session.scalar(stmt)

    def list_active(
        self, statuses: list[ReturnOpportunityStatus] | None = None
    ) -> list[ReturnOpportunity]:
        stmt = self._scoped()
        if statuses:
            stmt = stmt.where(ReturnOpportunity.status.in_(statuses))
        else:
            # Por padrao lista nao-fechadas e nao-descartadas
            stmt = stmt.where(
                ReturnOpportunity.status.not_in(
                    [
                        ReturnOpportunityStatus.CLOSED,
                        ReturnOpportunityStatus.DISMISSED,
                    ]
                )
            )
        stmt = stmt.order_by(ReturnOpportunity.due_date.asc())
        return list(self._session.scalars(stmt))

    def find_open_for_patient_and_procedure(
        self, patient_id: UUID, procedure_id: UUID
    ) -> list[ReturnOpportunity]:
        stmt = self._scoped().where(
            ReturnOpportunity.patient_id == patient_id,
            ReturnOpportunity.procedure_id == procedure_id,
            ReturnOpportunity.status.in_(
                [
                    ReturnOpportunityStatus.OPEN,
                    ReturnOpportunityStatus.CONTACTED,
                    ReturnOpportunityStatus.NO_RESPONSE,
                ]
            ),
        )
        return list(self._session.scalars(stmt))

    def close_for_patient_and_procedures(
        self,
        patient_id: UUID,
        procedure_ids: list[UUID],
        resolved_by_sale_id: UUID,
    ) -> int:
        """Fecha oportunidades abertas/contatadas do mesmo procedimento na nova venda (TASK-028)."""
        stmt = self._scoped().where(
            ReturnOpportunity.patient_id == patient_id,
            ReturnOpportunity.procedure_id.in_(procedure_ids),
            ReturnOpportunity.status.in_(
                [
                    ReturnOpportunityStatus.OPEN,
                    ReturnOpportunityStatus.CONTACTED,
                    ReturnOpportunityStatus.BOOKED,
                    ReturnOpportunityStatus.NO_RESPONSE,
                ]
            ),
        )
        opps = list(self._session.scalars(stmt))
        for opp in opps:
            opp.status = ReturnOpportunityStatus.CLOSED
            opp.resolved_by_sale_id = resolved_by_sale_id
        return len(opps)
