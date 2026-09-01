from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._session.scalars(
            select(User).where(User.id == user_id)
        ).one_or_none()

    def get_by_email(self, email: str) -> User | None:
        return self._session.scalars(
            select(User).where(func.lower(User.email) == email.lower())
        ).one_or_none()

    def list_all(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = (
            select(User)
            .order_by(User.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).all())

    def list_by_clinic(
        self, clinic_id: UUID, *, limit: int = 100, offset: int = 0
    ) -> list[User]:
        stmt = (
            select(User)
            .where(User.clinic_id == clinic_id)
            .order_by(User.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        count_val = self._session.scalar(select(func.count(User.id)))
        return count_val or 0

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def flush(self) -> None:
        self._session.flush()
