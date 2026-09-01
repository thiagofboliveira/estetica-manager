from uuid import uuid4

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
from app.repositories.clinic import ClinicRepository
from app.repositories.user import UserRepository
from app.services.clinic_service import ClinicService

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


def test_clinic_service_crud_and_users_count(db_session):
    clinic_repo = ClinicRepository(db_session)
    user_repo = UserRepository(db_session)
    clinic_svc = ClinicService(clinic_repo)

    # 1. Criação de Clínicas
    c1 = clinic_svc.create_clinic(
        name="Clínica Alpha",
        document="11.222.333/0001-44",
        plan="premium",
    )
    c2 = clinic_svc.create_clinic(
        name="Clínica Beta",
        document="22.333.444/0001-55",
        plan="standard",
    )
    db_session.commit()

    # 2. Adiciona usuários vinculados
    u1 = User(
        id=uuid4(),
        clinic_id=c1.id,
        name="Dra. Alpha 1",
        email="alpha1@test.com",
        role="admin",
        is_active=True,
    )
    u2 = User(
        id=uuid4(),
        clinic_id=c1.id,
        name="Dra. Alpha 2",
        email="alpha2@test.com",
        role="professional",
        is_active=True,
    )
    u3 = User(
        id=uuid4(),
        clinic_id=c2.id,
        name="Dra. Beta 1",
        email="beta1@test.com",
        role="admin",
        is_active=True,
    )
    user_repo.add(u1)
    user_repo.add(u2)
    user_repo.add(u3)
    db_session.commit()

    # 3. Listagem enriquecida com users_count
    clinics = clinic_svc.list_clinics()
    assert len(clinics) == 2
    alpha_clinic = next(c for c in clinics if c["name"] == "Clínica Alpha")
    beta_clinic = next(c for c in clinics if c["name"] == "Clínica Beta")
    assert alpha_clinic["users_count"] == 2
    assert beta_clinic["users_count"] == 1

    # 4. Atualização e Inativação
    clinic_svc.update_clinic(c1.id, name="Clínica Alpha Prime", plan="enterprise")
    clinic_svc.deactivate_clinic(c2.id)
    db_session.commit()

    assert clinic_svc.get_clinic(c1.id).name == "Clínica Alpha Prime"
    assert clinic_svc.get_clinic(c1.id).plan == "enterprise"
    assert clinic_svc.get_clinic(c2.id).is_active is False


def test_tenant_user_isolation_between_clinics(db_session):
    clinic_repo = ClinicRepository(db_session)
    user_repo = UserRepository(db_session)

    c_a = clinic_repo.add(Clinic(id=uuid4(), name="Clínica A", plan="standard", is_active=True))
    c_b = clinic_repo.add(Clinic(id=uuid4(), name="Clínica B", plan="standard", is_active=True))

    admin_a = user_repo.add(
        User(id=uuid4(), clinic_id=c_a.id, name="Admin A", email="admina@test.com", role="admin", is_active=True)
    )
    user_repo.add(
        User(id=uuid4(), clinic_id=c_a.id, name="User A", email="usera@test.com", role="user", is_active=True)
    )

    user_repo.add(
        User(id=uuid4(), clinic_id=c_b.id, name="Admin B", email="adminb@test.com", role="admin", is_active=True)
    )
    user_b = user_repo.add(
        User(id=uuid4(), clinic_id=c_b.id, name="User B", email="userb@test.com", role="user", is_active=True)
    )
    db_session.commit()

    app.dependency_overrides[_db] = lambda: db_session
    client = TestClient(app)

    # 1. Admin A só enxerga usuários da Clínica A
    app.dependency_overrides[get_current_professional_id] = lambda: admin_a.id
    res_a = client.get("/api/v1/users")
    assert res_a.status_code == 200
    users_a = res_a.json()
    assert len(users_a) == 2
    assert all(u["email"] in ("admina@test.com", "usera@test.com") for u in users_a)

    # 2. Admin A não consegue editar nem inativar User B da Clínica B (retorna 404)
    res_edit_cross = client.put(f"/api/v1/users/{user_b.id}", json={"name": "Hacked"})
    assert res_edit_cross.status_code == 404
    assert "não encontrado na clínica" in res_edit_cross.json()["detail"]

    res_del_cross = client.delete(f"/api/v1/users/{user_b.id}")
    assert res_del_cross.status_code == 404

    # 3. Admin A cria usuário -> automaticamente associado a c_a
    res_create = client.post("/api/v1/users", json={"name": "Novo A", "email": "novoa@test.com", "role": "receptionist"})
    assert res_create.status_code == 201
    assert res_create.json()["clinic_id"] == str(c_a.id)

    app.dependency_overrides.clear()


def test_super_admin_saas_platform_endpoints(db_session):
    clinic_repo = ClinicRepository(db_session)
    user_repo = UserRepository(db_session)

    # Super Admin Global (clinic_id = None, is_superuser = True)
    global_admin = user_repo.add(
        User(id=uuid4(), clinic_id=None, name="Super Global", email="super@platform.com", role="superadmin", is_superuser=True, is_active=True)
    )
    clinic_one = clinic_repo.add(Clinic(id=uuid4(), name="Matriz", plan="enterprise", is_active=True))
    db_session.commit()

    app.dependency_overrides[_db] = lambda: db_session
    app.dependency_overrides[_system_db] = lambda: db_session
    app.dependency_overrides[get_current_professional_id] = lambda: global_admin.id
    client = TestClient(app)

    # 1. POST /api/v1/super-admin/clinics
    res_new_clinic = client.post(
        "/api/v1/super-admin/clinics",
        json={"name": "Nova Filial Sul", "document": "99.888.777/0001-66", "plan": "pro"},
    )
    assert res_new_clinic.status_code == 201
    new_clinic_id = res_new_clinic.json()["id"]

    # 2. GET /api/v1/super-admin/clinics
    res_list_clinics = client.get("/api/v1/super-admin/clinics")
    assert res_list_clinics.status_code == 200
    assert len(res_list_clinics.json()) == 2

    # 3. PUT & DELETE /api/v1/super-admin/clinics/{id}
    res_put = client.put(f"/api/v1/super-admin/clinics/{new_clinic_id}", json={"plan": "enterprise"})
    assert res_put.status_code == 200
    assert res_put.json()["plan"] == "enterprise"

    res_del = client.delete(f"/api/v1/super-admin/clinics/{new_clinic_id}")
    assert res_del.status_code == 200
    assert res_del.json()["is_active"] is False

    # 4. POST /api/v1/super-admin/users vinculando à clínica
    res_create_user = client.post(
        "/api/v1/super-admin/users",
        json={
            "name": "Gerente Filial",
            "email": "gerente@filial.com",
            "role": "admin",
            "clinic_id": new_clinic_id,
        },
    )
    assert res_create_user.status_code == 201
    created_user_id = res_create_user.json()["id"]
    assert res_create_user.json()["clinic_id"] == new_clinic_id

    # 5. GET /api/v1/super-admin/users (lista com nome da clínica)
    res_all_users = client.get("/api/v1/super-admin/users")
    assert res_all_users.status_code == 200
    assert len(res_all_users.json()) >= 2
    gerente_found = next(u for u in res_all_users.json() if u["id"] == created_user_id)
    assert gerente_found["clinic_name"] == "Nova Filial Sul"

    # 6. PUT /api/v1/super-admin/users/{id} transferindo de clínica
    res_transfer = client.put(
        f"/api/v1/super-admin/users/{created_user_id}",
        json={"clinic_id": str(clinic_one.id)},
    )
    assert res_transfer.status_code == 200
    assert res_transfer.json()["clinic_id"] == str(clinic_one.id)

    app.dependency_overrides.clear()
