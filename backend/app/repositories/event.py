"""EventRepository — append-only de propósito (G-13).

Não expõe update() nem delete(): um evento é um fato imutável do que
aconteceu, não um registro editável. add() reaproveita o de
TenantRepository (carimba professional_id, ver base.py).
"""

from sqlalchemy import func, select

from app.models.event import Event
from app.repositories.base import TenantRepository


class EventRepository(TenantRepository[Event]):
    model = Event

    def list_by_name(self, name: str) -> list[Event]:
        stmt = self._scoped().where(Event.name == name).order_by(Event.created_at.asc())
        return list(self._session.scalars(stmt))

    def has_event(self, name: str) -> bool:
        """Usado para os eventos "first_*" — dispara só na primeira
        ocorrência (ex.: first_sale_recorded), não em toda venda."""
        stmt = self._scoped().where(Event.name == name).limit(1)
        return self._session.scalars(stmt).first() is not None

    def count_by_name(self, name: str) -> int:
        """Retorna o número total de ocorrências de um evento para o tenant."""
        stmt = select(func.count()).select_from(self.model).where(
            self.model.professional_id == self._professional_id,
            self.model.name == name,
        )
        return self._session.scalar(stmt) or 0

    def get_first_by_name(self, name: str) -> Event | None:
        """Retorna o primeiro registro de um determinado evento."""
        stmt = self._scoped().where(Event.name == name).order_by(Event.created_at.asc()).limit(1)
        return self._session.scalars(stmt).first()

