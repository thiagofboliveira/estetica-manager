from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import _db, _system_db, get_current_professional_id
from app.main import app
from app.models.clinic import Clinic
from app.models.professional import Professional
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.system_service import SystemService
from app.services.user_service import UserService

# SQLite in-memory engine para testes unitários isolados
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def setup_db():
    Clinic.__table__.create(bind=TEST_ENGINE, checkfirst=True)
    User.__table__.create(bind=TEST_ENGINE, checkfirst=True)
    Professional.__table__.create(bind=TEST_ENGINE, checkfirst=True)
    yield
    app.dependency_overrides.clear()
    Professional.__table__.drop(bind=TEST_ENGINE, checkfirst=True)
    User.__table__.drop(bind=TEST_ENGINE, checkfirst=True)
    Clinic.__table__.drop(bind=TEST_ENGINE, checkfirst=True)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_system_service_status_and_setup(db_session):
    repo = UserRepository(db_session)
    system_svc = SystemService(repo, db_session)

    # 1. Status inicial vazio
    status = system_svc.get_status()
    assert status["is_initialized"] is False
    assert status["users_count"] == 0

    # 2. Setup root
    root_user = system_svc.setup_root(
        clinic_name="Clínica Teste",
        admin_name="Admin Master",
        email="root@clinica.com",
    )
    db_session.commit()

    assert root_user.role == "superadmin"
    assert root_user.is_superuser is True
    assert root_user.email == "root@clinica.com"

    # 3. Status após setup
    status2 = system_svc.get_status()
    assert status2["is_initialized"] is True
    assert status2["users_count"] == 1

    # 4. Tentativa de segundo setup bloqueada
    with pytest.raises(ValueError, match="Sistema já inicializado"):
        system_svc.setup_root(
            clinic_name="Outra",
            admin_name="Tentativa",
            email="outro@clinica.com",
        )


def test_user_service_crud_rules(db_session):
    repo = UserRepository(db_session)
    user_svc = UserService(repo)

    # Criar admin
    admin_id = uuid4()
    admin = User(
        id=admin_id,
        name="Admin",
        email="admin@test.com",
        role="admin",
        is_superuser=False,
        is_active=True,
    )
    repo.add(admin)
    db_session.commit()

    # Criar novo profissional pela API
    new_user = user_svc.create_user(
        name="Dr. João",
        email="joao@test.com",
        role="professional",
    )
    db_session.commit()
    assert new_user.name == "Dr. João"
    assert new_user.role == "professional"

    # Listar
    users = user_svc.list_users()
    assert len(users) == 2

    # Bloquear criação com email duplicado
    with pytest.raises(ValueError, match="já está em uso"):
        user_svc.create_user(name="Outro", email="joao@test.com")

    # Bloquear auto-inativação
    with pytest.raises(ValueError, match="Não é permitido inativar o próprio usuário"):
        user_svc.deactivate_user(admin_id, current_user_id=admin_id)

    # Inativar outro usuário com sucesso
    user_svc.deactivate_user(new_user.id, current_user_id=admin_id)
    db_session.commit()

    updated = user_svc.get_user(new_user.id)
    assert updated.is_active is False


def test_system_and_users_api_endpoints(db_session):
    def override_system_db():
        yield db_session

    app.dependency_overrides[_system_db] = override_system_db
    client = TestClient(app)

    # 1. GET /api/v1/system/status
    res = client.get("/api/v1/system/status")
    assert res.status_code == 200
    assert res.json() == {"is_initialized": False, "users_count": 0}

    # 2. POST /api/v1/system/setup
    setup_payload = {
        "clinic_name": "Lumière Estética",
        "admin_name": "Dra. Super Admin",
        "email": "super@lumiere.com",
    }
    res_setup = client.post("/api/v1/system/setup", json=setup_payload)
    assert res_setup.status_code == 201
    superadmin_data = res_setup.json()
    assert superadmin_data["role"] == "superadmin"
    assert superadmin_data["is_superuser"] is True
    superadmin_id = superadmin_data["id"]

    # 3. GET /api/v1/system/status agora é true
    res2 = client.get("/api/v1/system/status")
    assert res2.status_code == 200
    assert res2.json() == {"is_initialized": True, "users_count": 1}

    # 4. Criar um usuário regular para testar RBAC
    user_id = uuid4()
    regular_user = User(
        id=user_id,
        clinic_id=UUID(superadmin_data["clinic_id"]),
        name="Atendente",
        email="atendente@lumiere.com",
        role="user",
        is_superuser=False,
        is_active=True,
    )
    db_session.add(regular_user)
    db_session.commit()

    # Helpers de override para requests autenticados
    def make_auth_override(current_id):
        def override_prof_id():
            return current_id

        def override_tenant_db():
            yield db_session

        return override_prof_id, override_tenant_db

    # 5. Tentativa de listar usuários por usuário comum -> 403
    app.dependency_overrides[get_current_professional_id] = lambda: regular_user.id
    app.dependency_overrides[_db] = lambda: db_session
    res_forbidden = client.get("/api/v1/users")
    assert res_forbidden.status_code == 403
    assert "Acesso restrito" in res_forbidden.json()["detail"]

    # 6. Admin lista usuários -> 200
    app.dependency_overrides[get_current_professional_id] = lambda: UUID(superadmin_id)
    res_users = client.get("/api/v1/users")
    assert res_users.status_code == 200
    assert len(res_users.json()) == 2

    # 7. Admin cria usuário -> 201
    res_create = client.post(
        "/api/v1/users",
        json={"name": "Recepção", "email": "recepcao@lumiere.com", "role": "receptionist"},
    )
    assert res_create.status_code == 201
    created_id = res_create.json()["id"]

    # 8. Admin edita usuário -> 200
    res_update = client.put(f"/api/v1/users/{created_id}", json={"name": "Recepção Central"})
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Recepção Central"

    # 9. Admin inativa usuário -> 200
    res_del = client.delete(f"/api/v1/users/{created_id}")
    assert res_del.status_code == 200
    assert res_del.json()["is_active"] is False

    # 10. Admin não pode inativar a si mesmo -> 400
    res_del_self = client.delete(f"/api/v1/users/{superadmin_id}")
    assert res_del_self.status_code == 400
    assert "próprio usuário" in res_del_self.json()["detail"]

    # Cleanup overrides
    app.dependency_overrides.clear()
