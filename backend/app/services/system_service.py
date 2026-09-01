from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.clinic import Clinic
from app.models.professional import Professional
from app.models.user import User
from app.repositories.user import UserRepository


class SystemService:
    def __init__(self, user_repo: UserRepository, session: Session) -> None:
        self._user_repo = user_repo
        self._session = session

    def get_status(self) -> dict:
        count = self._user_repo.count()
        return {
            "is_initialized": count > 0,
            "users_count": count,
        }

    def setup_root(
        self,
        clinic_name: str,
        admin_name: str,
        email: str,
        password: str | None = None,
    ) -> User:
        if self._user_repo.count() > 0:
            raise ValueError("Sistema já inicializado com usuários existentes")

        clinic_id = uuid4()
        clinic = Clinic(
            id=clinic_id,
            name=clinic_name.strip() or "Clínica Matriz",
            plan="enterprise",
            is_active=True,
        )
        self._session.add(clinic)

        root_id = uuid4()
        user = User(
            id=root_id,
            clinic_id=clinic_id,
            name=admin_name.strip(),
            email=email.lower().strip(),
            role="superadmin",
            is_superuser=True,
            is_active=True,
        )
        self._user_repo.add(user)

        # Cria o tenant inicial associado ao primeiro usuário administrador
        professional = Professional(
            id=root_id,
            clinic_id=clinic_id,
            user_id=root_id,
            name=clinic_name.strip() or admin_name.strip(),
            timezone=settings.DEFAULT_TIMEZONE,
            is_active=True,
        )
        self._session.add(professional)
        self._session.flush()

        return user
