from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select

from app.domain.sales.session_state_machine import SessionStatus
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
                        SessionStatus.RESCHEDULED,
                    ]
                ),
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
        """Nº de sessões concluídas no período, base para "atendimentos"
        (§13.1) — denominador diferente de "nº de vendas" de propósito.

        Invariante I4 (MVP v6 §3): converte completed_at para o fuso da
        PROFISSIONAL antes de truncar por dia — nunca confia no fuso de
        sessão do Postgres (hoje é UTC neste ambiente, mas depender
        disso implicitamente reintroduziria o mesmo bug corrigido em
        sold_at, só de forma silenciosa se a config do banco mudar).
        `AT TIME ZONE tz` sobre um TIMESTAMPTZ devolve o instante local
        como TIMESTAMP naive, pronto para comparar com DATE."""
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
