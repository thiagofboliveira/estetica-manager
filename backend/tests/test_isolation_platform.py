"""Testes de isolamento cross-tenant para tabelas de plataforma:
clinics, users e professionals com RLS e repositórios escopados (S-02a, S-02b, S-02c).
"""

from contextlib import suppress
from uuid import uuid4

from sqlalchemy import select

from app.db.session import engine, get_tenant_session, unsafe_session_without_tenant
from app.models.clinic import Clinic
from app.models.professional import Professional
from app.models.user import User
from app.repositories.clinic import ClinicRepository
from app.repositories.user import UserRepository


def test_cross_tenant_isolation_clinics_users_and_professionals():
    """Valida que uma profissional de uma clínica não consegue ler nem acessar
    clínicas, usuários ou profissionais de outra clínica via RLS ou Repository.
    """
    # 1. Provisiona duas clínicas e dois tenants distintos via unsafe_session (setup/superadmin)
    clinic_a_id = uuid4()
    clinic_b_id = uuid4()
    user_a_id = uuid4()
    user_b_id = uuid4()

    with unsafe_session_without_tenant("provision test platform isolation") as session:
        clinic_a = Clinic(id=clinic_a_id, name=f"Clínica Alfa {clinic_a_id.hex[:4]}")
        clinic_b = Clinic(id=clinic_b_id, name=f"Clínica Beta {clinic_b_id.hex[:4]}")

        user_a = User(
            id=user_a_id,
            clinic_id=clinic_a_id,
            name="Doutora Alfa",
            email=f"alfa_{user_a_id.hex[:6]}@example.com",
            role="admin",
            is_active=True,
        )
        user_b = User(
            id=user_b_id,
            clinic_id=clinic_b_id,
            name="Doutora Beta",
            email=f"beta_{user_b_id.hex[:6]}@example.com",
            role="admin",
            is_active=True,
        )

        prof_a = Professional(
            id=user_a_id,
            user_id=user_a_id,
            clinic_id=clinic_a_id,
            name="Doutora Alfa",
            timezone="America/Sao_Paulo",
            is_active=True,
        )
        prof_b = Professional(
            id=user_b_id,
            user_id=user_b_id,
            clinic_id=clinic_b_id,
            name="Doutora Beta",
            timezone="America/Sao_Paulo",
            is_active=True,
        )

        session.add_all([clinic_a, clinic_b])
        session.flush()
        session.add_all([user_a, user_b])
        session.flush()
        session.add_all([prof_a, prof_b])
        session.commit()

    # 2. Testa acesso a partir do contexto do Tenant Alfa (user_a / prof_a)
    gen_a = get_tenant_session(user_a_id)
    session_a = next(gen_a)
    try:
        user_repo_a = UserRepository(session_a, clinic_id=clinic_a_id)
        clinic_repo_a = ClinicRepository(session_a, clinic_id=clinic_a_id)

        # 2.1 Isolamento de Clínicas
        # Consegue ver a sua própria clínica
        assert clinic_repo_a.get_by_id(clinic_a_id) is not None
        assert session_a.get(Clinic, clinic_a_id) is not None

        # RLS e Repo bloqueiam o acesso à Clínica Beta
        assert clinic_repo_a.get_by_id(clinic_b_id) is None
        assert session_a.get(Clinic, clinic_b_id) is None

        # 2.2 Isolamento de Usuários
        # Consegue ver a si mesma
        assert user_repo_a.get_by_id(user_a_id) is not None
        assert session_a.get(User, user_a_id) is not None

        # RLS e Repo bloqueiam a consulta à Doutora Beta
        assert user_repo_a.get_by_id(user_b_id) is None
        assert session_a.get(User, user_b_id) is None

        # Listagem nunca vaza usuários da Clínica Beta
        users_visiveis = user_repo_a.list_all()
        user_ids_visiveis = {u.id for u in users_visiveis}
        assert user_a_id in user_ids_visiveis
        assert user_b_id not in user_ids_visiveis

        # 2.3 Isolamento de Profissionais
        assert session_a.get(Professional, user_a_id) is not None
        assert session_a.get(Professional, user_b_id) is None

        # Query crua no banco PostgreSQL respeita o RLS forçado da role estetica_app
        all_profs = list(session_a.scalars(select(Professional)).all())
        all_prof_ids = {p.id for p in all_profs}
        assert user_a_id in all_prof_ids
        assert user_b_id not in all_prof_ids
        # 2.4 Proteção contra escrita cross-tenant (S-02b)
        import pytest

        with pytest.raises(ValueError, match="clínica alheia"):
            user_repo_a.add(
                User(
                    id=uuid4(),
                    clinic_id=clinic_b_id,
                    name="Invasor",
                    email=f"invasor_{uuid4().hex[:6]}@example.com",
                )
            )

        # 2.5 Contagem de usuários de outra clínica é isolada
        assert clinic_repo_a.count_users(clinic_b_id) == 0
    finally:
        with suppress(StopIteration):
            next(gen_a)

    # 3. Testa visão de Super Admin (unsafe_session_without_tenant)
    with unsafe_session_without_tenant(
        "test superadmin platform visibility"
    ) as admin_session:
        super_user_repo = UserRepository(admin_session, clinic_id=None)
        super_clinic_repo = ClinicRepository(admin_session, clinic_id=None)

        # Superadmin enxerga ambas as clínicas e ambos os usuários
        assert super_clinic_repo.get_by_id(clinic_a_id) is not None
        assert super_clinic_repo.get_by_id(clinic_b_id) is not None
        assert super_user_repo.get_by_id(user_a_id) is not None
        assert super_user_repo.get_by_id(user_b_id) is not None


def test_pool_checkin_resets_all_platform_tenant_gucs():
    """Garante que app.professional_id, app.clinic_id e app.bypass_tenant
    são limpos no checkin do pool e não vazam entre requests.
    """
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    user_id = uuid4()
    # Executa sessão com tenant fixado
    gen = get_tenant_session(user_id)
    session = next(gen)
    try:
        pid = session.execute(
            text("SELECT current_setting('app.professional_id', true)")
        ).scalar()
        assert pid == str(user_id)
    finally:
        with suppress(StopIteration):
            next(gen)

    # Agora abre nova conexão crua do pool: nenhum GUC deve persistir
    with Session(engine) as fresh_session:
        pid_after = fresh_session.execute(
            text("SELECT current_setting('app.professional_id', true)")
        ).scalar()
        cid_after = fresh_session.execute(
            text("SELECT current_setting('app.clinic_id', true)")
        ).scalar()
        bypass_after = fresh_session.execute(
            text("SELECT current_setting('app.bypass_tenant', true)")
        ).scalar()

        assert pid_after in (None, "")
        assert cid_after in (None, "")
        assert bypass_after in (None, "")
