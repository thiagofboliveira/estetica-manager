"""SessionService — orquestra PATCH /sessions/{id} (T-016).

Camada fina: valida a transição via domain, persiste, e aciona a
checagem de exaustão do motor de retorno (T-025) na mesma transação.
"""

from uuid import UUID

from app.core.tz import now_in_timezone
from app.domain.sales.session_state_machine import SessionStatus, validate_transition
from app.models.session import Session as SessionModel
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.services.retention_service import RetentionService


class SessionNotFoundError(Exception):
    pass


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        sale_item_repo: SaleItemRepository,
        sale_repo: SaleRepository,
        retention_service: RetentionService,
        professional_timezone: str,
    ) -> None:
        self._sessions = session_repo
        self._sale_items = sale_item_repo
        self._sales = sale_repo
        self._retention = retention_service
        self._professional_timezone = professional_timezone

    def update_status(self, session_id: UUID, new_status: SessionStatus) -> SessionModel:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError()

        validate_transition(session.status, new_status)
        session.status = new_status
        if new_status == SessionStatus.COMPLETED:
            session.completed_at = now_in_timezone(self._professional_timezone)
        self._sessions.flush()

        sale_item = self._sale_items.get(session.sale_item_id)
        sale = self._sales.get(sale_item.sale_id)
        self._retention.check_and_create_opportunity(
            sale_item=sale_item,
            patient_id=sale.patient_id,
            professional_timezone=self._professional_timezone,
        )

        return session
