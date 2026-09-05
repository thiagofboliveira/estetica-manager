from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.domain.sales.session_state_machine import SessionStatus
from app.models.sale_item import SaleItem
from app.models.session import Session
from app.repositories.base import TenantRepository


class SessionRepository(TenantRepository[Session]):
    model = Session

    def get_by_id(self, session_id: UUID) -> Session | None:
        stmt = self._scoped().where(Session.id == session_id)
        return self._session.scalar(stmt)

    def list_for_sale_item(self, sale_item_id: UUID) -> list[Session]:
        stmt = (
            self._scoped()
            .where(Session.sale_item_id == sale_item_id)
            .order_by(Session.sequence_number)
        )
        return list(self._session.scalars(stmt))

    def list_scheduled_in_range(
        self, start_dt: datetime, end_dt: datetime
    ) -> list[Session]:
        stmt = (
            self._scoped()
            .where(
                Session.scheduled_at.is_not(None),
                Session.scheduled_at >= start_dt,
                Session.scheduled_at <= end_dt,
                Session.status.in_(
                    [
                        SessionStatus.SCHEDULED,
                        SessionStatus.CONFIRMED,
                        SessionStatus.COMPLETED,
                        SessionStatus.NO_SHOW,
                    ]
                ),
            )
            .order_by(Session.scheduled_at.asc())
        )
        return list(self._session.scalars(stmt))

    def list_unconfirmed_in_range(
        self, start_dt: datetime, end_dt: datetime
    ) -> list[Session]:
        """Lista sessões agendadas que ainda não foram confirmadas (confirmed_at IS NULL)."""
        stmt = (
            self._scoped()
            .where(
                Session.scheduled_at.is_not(None),
                Session.scheduled_at >= start_dt,
                Session.scheduled_at <= end_dt,
                Session.status == SessionStatus.SCHEDULED,
                Session.confirmed_at.is_(None),
            )
            .order_by(Session.scheduled_at.asc())
        )
        return list(self._session.scalars(stmt))

    def find_conflicts(
        self, scheduled_at: datetime, exclude_session_id: UUID | None = None
    ) -> list[Session]:
        stmt = self._scoped().where(
            Session.scheduled_at == scheduled_at,
            Session.status.in_([SessionStatus.SCHEDULED, SessionStatus.CONFIRMED]),
        )
        if exclude_session_id:
            stmt = stmt.where(Session.id != exclude_session_id)
        return list(self._session.scalars(stmt))

    def list_open_package_sessions(self) -> list[Session]:
        stmt = (
            self._scoped()
            .where(Session.status == SessionStatus.PENDING)
            .order_by(Session.sale_item_id, Session.sequence_number)
        )
        return list(self._session.scalars(stmt))

    def count_completed_in_period(
        self, date_from: date, date_to: date, timezone_name: str
    ) -> int:
        local_date = func.date(Session.completed_at.op("AT TIME ZONE")(timezone_name))
        stmt = (
            select(func.count())
            .select_from(Session)
            .where(Session.professional_id == self._professional_id)
            .where(Session.status == SessionStatus.COMPLETED)
            .where(local_date >= date_from)
            .where(local_date <= date_to)
        )
        return int(self._session.scalar(stmt) or 0)

    def count_completed_by_procedure_in_period(
        self, date_from: date, date_to: date, timezone_name: str
    ) -> dict[UUID, int]:
        """Nº de sessões COMPLETED por procedure_id — base de "atendimento"
        (I5: nº de atendimentos é Sessão, não Sale/Item). Usado pelo
        ranking de procedimentos para não confundir "sessão vendida"
        (SaleItem.quantity, inclui PENDING) com "sessão realizada"."""
        local_date = func.date(Session.completed_at.op("AT TIME ZONE")(timezone_name))
        stmt = (
            select(SaleItem.procedure_id, func.count())
            .select_from(Session)
            .join(SaleItem, SaleItem.id == Session.sale_item_id)
            .where(Session.professional_id == self._professional_id)
            .where(Session.status == SessionStatus.COMPLETED)
            .where(local_date >= date_from)
            .where(local_date <= date_to)
            .group_by(SaleItem.procedure_id)
        )
        return dict(self._session.execute(stmt).all())

    def count_no_show_in_period(
        self, date_from: date, date_to: date, timezone_name: str
    ) -> int:
        """Nº de sessões NO_SHOW no período (EPIC-S2-02, TASK-BACK-S2-11)."""
        # Utiliza scheduled_at ou completed_at local
        local_date = func.date(Session.scheduled_at.op("AT TIME ZONE")(timezone_name))
        stmt = (
            select(func.count())
            .select_from(Session)
            .where(Session.professional_id == self._professional_id)
            .where(Session.status == SessionStatus.NO_SHOW)
            .where(local_date >= date_from)
            .where(local_date <= date_to)
        )
        return int(self._session.scalar(stmt) or 0)

    def list_no_show_avoided_in_period(
        self, date_from: date, date_to: date, timezone_name: str
    ) -> list[tuple[Session, Decimal]]:
        """G-11: sessões que passaram pelo fluxo anti-no-show
        (confirmed_at preenchido — a profissional confirmou via
        NoShowAlert, ver GET /sessions/unconfirmed) e terminaram
        COMPLETED, não NO_SHOW. É o proxy mais direto disponível hoje de
        "no-show evitado": sem essa confirmação explícita, não há como
        diferenciar uma sessão que "não faltaria de qualquer jeito" de
        uma que só compareceu por causa do lembrete — este critério é
        conservador (conta só quem passou pelo fluxo de risco), não
        universal (não conta confirmações informais fora do produto).

        Retorna junto o valor da sessão (SaleItem.unit_price, congelado
        no momento da venda — I3, I5: dinheiro nunca vive na Session).

        Usa COALESCE(completed_at, scheduled_at) para a data local, não
        só scheduled_at: venda avulsa completada na hora tem
        scheduled_at NULL (nunca foi "agendada" antes de acontecer) —
        completed_at é quando ela de fato ocorreu, a data que importa
        para "isto aconteceu neste período".
        """
        event_ts = func.coalesce(Session.completed_at, Session.scheduled_at)
        local_date = func.date(event_ts.op("AT TIME ZONE")(timezone_name))
        stmt = (
            select(Session, SaleItem.unit_price)
            .select_from(Session)
            .join(SaleItem, SaleItem.id == Session.sale_item_id)
            .where(Session.professional_id == self._professional_id)
            .where(Session.status == SessionStatus.COMPLETED)
            .where(Session.confirmed_at.is_not(None))
            .where(local_date >= date_from)
            .where(local_date <= date_to)
            .order_by(event_ts.asc())
        )
        return [(row[0], row[1]) for row in self._session.execute(stmt)]
