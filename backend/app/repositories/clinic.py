from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.clinic import Clinic
from app.models.user import User


class ClinicRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, clinic_id: UUID) -> Clinic | None:
        return self._session.scalars(
            select(Clinic).where(Clinic.id == clinic_id)
        ).one_or_none()

    def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Clinic]:
        stmt = (
            select(Clinic)
            .order_by(Clinic.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        count_val = self._session.scalar(select(func.count(Clinic.id)))
        return count_val or 0

    def count_users(self, clinic_id: UUID) -> int:
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
