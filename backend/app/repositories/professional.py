"""ProfessionalRepository — não usa TenantRepository porque Professional
É o tenant (tem `id`, não `professional_id`) — não filtra por si mesma.

RLS não se aplica aqui do mesmo jeito: a policy de `professionals` (ver
migration 0001) usa `id = current_setting(...)`, não `professional_id`.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.professional import Professional


class ProfessionalRepository:
    def __init__(self, session: Session, professional_id: UUID) -> None:
        self._session = session
        self._professional_id = professional_id

    def get_current(self) -> Professional:
        """A própria profissional autenticada — sempre existe (é quem o
        JWT resolveu), então None aqui seria bug de outra camada."""
        professional = self._session.scalars(
            select(Professional).where(Professional.id == self._professional_id)
        ).one_or_none()
        if professional is None:
            raise LookupError(
                f"professional autenticado não encontrado: {self._professional_id}"
            )
        return professional
