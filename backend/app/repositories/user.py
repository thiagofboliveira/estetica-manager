from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Repositório de usuários com escopo de clínica (S-02b).

    Quando instanciado com clinic_id, aplica filtro de isolamento
    no nível da aplicação como defesa em profundidade (RLS protege no banco).
    Quando clinic_id é None, opera em modo plataforma global (Super Admin).
    """

    def __init__(self, session: Session, clinic_id: UUID | None = None) -> None:
        self._session = session
        self._clinic_id = clinic_id

    def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if self._clinic_id is not None:
            stmt = stmt.where(User.clinic_id == self._clinic_id)
        return self._session.scalars(stmt).one_or_none()

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        if self._clinic_id is not None:
            stmt = stmt.where(User.clinic_id == self._clinic_id)
        return self._session.scalars(stmt).one_or_none()

    def list_all(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User)
        if self._clinic_id is not None:
            stmt = stmt.where(User.clinic_id == self._clinic_id)
        stmt = stmt.order_by(User.created_at.asc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt).all())

    def list_by_clinic(
        self, clinic_id: UUID, *, limit: int = 100, offset: int = 0
    ) -> list[User]:
        if self._clinic_id is not None and self._clinic_id != clinic_id:
            return []
        stmt = (
            select(User)
            .where(User.clinic_id == clinic_id)
            .order_by(User.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        stmt = select(func.count(User.id))
        if self._clinic_id is not None:
            stmt = stmt.where(User.clinic_id == self._clinic_id)
        count_val = self._session.scalar(stmt)
        return count_val or 0

    def add(self, user: User) -> User:
        if self._clinic_id is not None:
            if user.clinic_id is None:
                user.clinic_id = self._clinic_id
            elif user.clinic_id != self._clinic_id:
                raise ValueError(
                    f"Tentativa de criar usuário em clínica alheia: {user.clinic_id} != {self._clinic_id}"
                )
        self._session.add(user)
        self._session.flush()
        return user

    def flush(self) -> None:
        self._session.flush()
