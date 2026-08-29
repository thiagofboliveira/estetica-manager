"""Repository base — segunda camada de defesa de isolamento.

Contrato:
  - professional_id é obrigatório no construtor (sem default)
  - NENHUM método público devolve Query/Select sem filtro aplicado
  - a sessão é privada (_session): autocomplete não sugere query() cru
  - add() CARIMBA o tenant em vez de confiar em quem chamou

RLS (terceira camada, no banco) cobre o que escapar daqui — mas o
objetivo deste repository é que nada precise escapar.
"""

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.base import TenantModel


class TenantRepository[M: TenantModel]:
    model: type[M]

    def __init__(self, session: Session, professional_id: UUID) -> None:
        if professional_id is None:
            raise ValueError("professional_id é obrigatório")
        self._session = session
        self._professional_id = professional_id

    def _scoped(self) -> Select[tuple[M]]:
        """ÚNICA fonte de SELECT do repositório — todo método de leitura
        passa por aqui, então o filtro de tenant não tem como ser
        esquecido em um método novo."""
        return select(self.model).where(
            self.model.professional_id == self._professional_id
        )

    def get(self, id_: UUID) -> M | None:
        return self._session.scalars(
            self._scoped().where(self.model.id == id_)
        ).one_or_none()

    def list(self, *, limit: int = 50, offset: int = 0) -> list[M]:
        stmt = (
            self._scoped()
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))

    def add(self, obj: M) -> M:
        """Carimba o tenant em vez de confiar em quem chamou. Se o
        objeto já veio com professional_id de outro tenant, é bug —
        falha alto em vez de gravar silenciosamente errado."""
        if obj.professional_id not in (None, self._professional_id):
            raise ValueError(
                f"tentativa de gravar em tenant alheio: "
                f"{obj.professional_id} != {self._professional_id}"
            )
        obj.professional_id = self._professional_id
        self._session.add(obj)
        self._session.flush()
        return obj

    def delete(self, obj: M) -> None:
        if obj.professional_id != self._professional_id:
            raise ValueError("delete cross-tenant bloqueado")
        self._session.delete(obj)

    def flush(self) -> None:
        """Para o service persistir mudanças em objeto já anexado (get →
        muta atributos → flush), sem expor a sessão inteira."""
        self._session.flush()
