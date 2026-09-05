"""Repositório para auditoria de aceite de Termos de Uso e Política LGPD (G-10)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.terms_acceptance import TermsAcceptance


class TermsAcceptanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record_acceptance(
        self,
        user_id: UUID,
        terms_version: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TermsAcceptance:
        acceptance = TermsAcceptance(
            user_id=user_id,
            terms_version=terms_version,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(acceptance)
        self._session.flush()
        return acceptance

    def list_by_user(self, user_id: UUID) -> list[TermsAcceptance]:
        stmt = (
            select(TermsAcceptance)
            .where(TermsAcceptance.user_id == user_id)
            .order_by(TermsAcceptance.accepted_at.desc())
        )
        return list(self._session.scalars(stmt).all())
