from datetime import date
from uuid import UUID

from sqlalchemy import exists, func, select

from app.domain.sales.session_state_machine import SessionStatus
from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem
from app.models.session import Session
from app.repositories.base import TenantRepository


class SessionRepository(TenantRepository[Session]):
    model = Session

    def list_for_sale_item(self, sale_item_id: UUID) -> list[Session]:
        stmt = self._scoped().where(Session.sale_item_id == sale_item_id).order_by(
            Session.sequence_number
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
        local_date = func.date(
            Session.completed_at.op("AT TIME ZONE")(timezone_name)
        )
        stmt = (
            select(func.count())
            .select_from(Session)
            .where(Session.professional_id == self._professional_id)
            .where(Session.status == SessionStatus.COMPLETED)
            .where(local_date >= date_from)
            .where(local_date <= date_to)
        )
        return int(self._session.scalar(stmt) or 0)

    def has_pending_session_in_period(self, date_from: date, date_to: date) -> bool:
        """T-022b, A-07: existe alguma sessão PENDING de uma venda ACTIVE
        com sold_at no período? Base do badge "lucro provisório" — sem
        isso o front não tem como saber, porque o endpoint é agregado
        (cost_realized só reflete sessões já concluídas/expiradas)."""
        stmt = exists(
            select(Session.id)
            .join(SaleItem, SaleItem.id == Session.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Session.professional_id == self._professional_id)
            .where(Session.status == SessionStatus.PENDING)
            .where(Sale.status == SaleStatus.ACTIVE)
            .where(Sale.sold_at >= date_from)
            .where(Sale.sold_at <= date_to)
        ).select()
        return bool(self._session.scalar(stmt))
