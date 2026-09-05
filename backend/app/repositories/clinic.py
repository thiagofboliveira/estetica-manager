from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.clinic import Clinic
from app.models.user import User


class ClinicRepository:
    """Repositório de clínicas com escopo opcional de isolamento (S-02b).

    Quando instanciado com clinic_id, impede visualização de dados de outras clínicas.
    Quando clinic_id é None, opera em modo plataforma global (Super Admin).
    """

    def __init__(self, session: Session, clinic_id: UUID | None = None) -> None:
        self._session = session
        self._clinic_id = clinic_id

    def get_by_id(self, clinic_id: UUID) -> Clinic | None:
        if self._clinic_id is not None and self._clinic_id != clinic_id:
            return None
        return self._session.scalars(
            select(Clinic).where(Clinic.id == clinic_id)
        ).one_or_none()

    def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Clinic]:
        stmt = select(Clinic)
        if self._clinic_id is not None:
            stmt = stmt.where(Clinic.id == self._clinic_id)
        stmt = stmt.order_by(Clinic.created_at.asc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        stmt = select(func.count(Clinic.id))
        if self._clinic_id is not None:
            stmt = stmt.where(Clinic.id == self._clinic_id)
        count_val = self._session.scalar(stmt)
        return count_val or 0

    def count_users(self, clinic_id: UUID) -> int:
        if self._clinic_id is not None and self._clinic_id != clinic_id:
            return 0
        count_val = self._session.scalar(
            select(func.count(User.id)).where(User.clinic_id == clinic_id)
        )
        return count_val or 0

    def add(self, clinic: Clinic) -> Clinic:
        self._session.add(clinic)
        self._session.flush()
        return clinic

    def flush(self) -> None:
        self._session.flush()
