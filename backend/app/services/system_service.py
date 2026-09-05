from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.supabase_admin import SupabaseAdminClient, SupabaseAdminError
from app.models.clinic import Clinic
from app.models.professional import Professional
from app.models.user import User
from app.repositories.user import UserRepository


class SystemSetupError(Exception):
    """Falha ao provisionar o usuário no Supabase Auth durante o setup —
    distinta de ValueError ("já inicializado"), para a rota devolver o
    HTTP certo em cada caso."""


class SystemService:
    def __init__(
        self,
        user_repo: UserRepository,
        session: Session,
        supabase_admin: SupabaseAdminClient | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._session = session
        # Injetável para teste (mock) — nunca instanciado aqui na falta de
        # SUPABASE_SERVICE_ROLE_KEY, porque isso quebraria get_status()
        # (rota pública, sem esse segredo) além do setup.
        self._supabase_admin = supabase_admin

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
    ) -> User:
        """B-01: NÃO recebe senha. User (I2) não tem password_hash de
        propósito — a fonte de verdade de identidade é o Supabase Auth.
        O fluxo antigo coletava uma senha na tela e a descartava
        silenciosamente (nunca era usada aqui); a correção é criar o
        usuário no Supabase Auth via Admin API (sem senha — o Supabase
        gera um magic-link de convite) e usar o MESMO UUID retornado
        como User.id/Professional.id, respeitando o mapeamento 1:1 que
        core/security.py já assume."""
        if self._user_repo.count() > 0:
            raise ValueError("Sistema já inicializado com usuários existentes")

        admin = self._supabase_admin or SupabaseAdminClient()
        normalized_email = email.lower().strip()
        try:
            root_id = admin.invite_user_by_email(
                normalized_email, redirect_to=settings.FRONTEND_URL
            )
        except SupabaseAdminError as exc:
            raise SystemSetupError(str(exc)) from exc

        clinic_id = uuid4()
        clinic = Clinic(
            id=clinic_id,
            name=clinic_name.strip() or "Clínica Matriz",
            plan="enterprise",
            is_active=True,
        )
        self._session.add(clinic)

        user = User(
            id=root_id,
            clinic_id=clinic_id,
            name=admin_name.strip(),
            email=normalized_email,
            role="superadmin",
            is_superuser=True,
            is_active=True,
        )
        try:
            self._user_repo.add(user)
            self._session.flush()

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
        except Exception:
            # Não deixar usuário órfão no Supabase Auth sem User/
            # Professional correspondente — o convite já foi enviado,
            # mas sem a linha local o login dele nunca resolveria
            # professional_id (ficaria preso num 401/404 silencioso).
            admin.delete_user(root_id)
            raise

        return user
