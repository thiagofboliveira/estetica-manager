"""EventRepository — append-only de propósito (G-13).

Não expõe update() nem delete(): um evento é um fato imutável do que
aconteceu, não um registro editável. add() reaproveita o de
TenantRepository (carimba professional_id, ver base.py).
"""

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
