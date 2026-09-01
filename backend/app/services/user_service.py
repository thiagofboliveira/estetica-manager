from uuid import UUID, uuid4

from app.core.config import settings
from app.models.professional import Professional
from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def list_users(self, clinic_id: UUID | None = None) -> list[User]:
        if clinic_id is not None:
            return self._user_repo.list_by_clinic(clinic_id)
        return self._user_repo.list_all()

    def get_user(self, user_id: UUID) -> User:
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError(f"Usuário {user_id} não encontrado")
        return user

    def create_user(
        self,
        name: str,
        email: str,
        role: str = "user",
        is_superuser: bool = False,
        clinic_id: UUID | None = None,
    ) -> User:
        existing = self._user_repo.get_by_email(email)
        if existing is not None:
            raise ValueError(f"E-mail {email} já está em uso")

        user_id = uuid4()
        user = User(
            id=user_id,
            clinic_id=clinic_id,
            name=name.strip(),
            email=email.lower().strip(),
            role=role,
            is_superuser=is_superuser,
            is_active=True,
        )
        self._user_repo.add(user)

        # Garante a criação da entidade Professional correspondente (tenant)
        professional = Professional(
            id=user_id,
            clinic_id=clinic_id,
            user_id=user_id,
            name=name.strip(),
            timezone=settings.DEFAULT_TIMEZONE,
            is_active=True,
        )
        self._user_repo._session.add(professional)
        self._user_repo.flush()
        return user

    def update_user(
        self,
        user_id: UUID,
        current_user_id: UUID,
        name: str | None = None,
        email: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
        clinic_id: UUID | None = None,
    ) -> User:
        user = self.get_user(user_id)

        if is_active is False and user_id == current_user_id:
            raise ValueError("Não é permitido inativar o próprio usuário logado")

        if name is not None:
            user.name = name.strip()
        if email is not None:
            normalized = email.lower().strip()
            if normalized != user.email:
                existing = self._user_repo.get_by_email(normalized)
                if existing is not None and existing.id != user_id:
                    raise ValueError(f"E-mail {email} já está em uso por outro usuário")
                user.email = normalized
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if is_superuser is not None:
            user.is_superuser = is_superuser
        if clinic_id is not None:
            user.clinic_id = clinic_id

        # Sincroniza entidade Professional
        prof = self._user_repo._session.get(Professional, user_id)
        if prof:
            if name is not None:
                prof.name = name.strip()
            if is_active is not None:
                prof.is_active = is_active
            if clinic_id is not None:
                prof.clinic_id = clinic_id
        else:
            prof = Professional(
                id=user_id,
                clinic_id=user.clinic_id,
                user_id=user_id,
                name=user.name,
                timezone=settings.DEFAULT_TIMEZONE,
                is_active=user.is_active,
            )
            self._user_repo._session.add(prof)

        self._user_repo.flush()
        return user

    def deactivate_user(self, user_id: UUID, current_user_id: UUID) -> User:
        return self.update_user(
            user_id=user_id,
            current_user_id=current_user_id,
            is_active=False,
        )
