from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.db.session import unsafe_session_without_tenant
from app.main import app
from app.models.clinic import Clinic
from app.models.patient import Patient
from app.models.professional import Professional
from app.models.user import User
from app.services.email_service import EmailService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_email_service_send_vip_card_email():
    email_svc = EmailService()
    success = email_svc.send_vip_card_email(
        recipient_email="paciente@example.com",
        patient_name="Mariana Souza",
        clinic_name="Clínica Bella",
        vip_tier="OURO",
        loyalty_points=350,
        credit_value=Decimal("175.00"),
        referral_code="LUM-MARI123",
        vip_card_url="https://app.lumina.com/clube-vip/LUM-MARI123",
        booking_url="https://app.lumina.com/agendar/bella",
    )
    assert success is True


def test_public_vip_card_endpoint_and_service(client: TestClient):
    clinic_id = uuid4()
    prof_id = uuid4()
    patient_id = uuid4()
    unique_code = f"VIP-{uuid4().hex[:6].upper()}"

    with unsafe_session_without_tenant("setup vip card test") as session:
        clinic = Clinic(id=clinic_id, name="Clínica Renovare")
        session.add(clinic)
        session.flush()

        user = User(
            id=prof_id,
            clinic_id=clinic_id,
            name="Dra. Paula Renovare",
            email=f"paula_{prof_id.hex[:6]}@example.com",
            role="admin",
            is_active=True,
        )
        session.add(user)
        session.flush()

        prof = Professional(
            id=prof_id,
            user_id=prof_id,
            clinic_id=clinic_id,
            name="Dra. Paula",
            slug=f"dra-paula-{prof_id.hex[:4]}",
            timezone="America/Sao_Paulo",
            is_active=True,
        )
        session.add(prof)
        session.flush()

        p = Patient(
            id=patient_id,
            professional_id=prof_id,
            name="Fernanda Lima",
            phone="+5511999998888",
            email="fernanda.lima@example.com",
            referral_code=unique_code,
            loyalty_points=120,
            vip_tier="SILVER",
            is_active=True,
            consent_whatsapp=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(p)
        session.flush()

    # 1. Rota pública sem token
    resp = client.get(f"/api/v1/loyalty/public-card/{unique_code}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["patient_first_name"] == "Fernanda"
    assert data["patient_full_name"] == "Fernanda Lima"
    assert data["clinic_name"] == "Clínica Renovare"
    assert data["vip_tier"] == "SILVER"
    assert data["loyalty_points"] == 120
    assert data["next_tier"] == "OURO"
    assert data["points_to_next_tier"] == 180  # 300 - 120
    assert data["referral_code"] == unique_code
    assert len(data["catalog_rewards"]) >= 3
    assert data["public_booking_slug"] == f"dra-paula-{prof_id.hex[:4]}"

    # 2. Rota pública com código inexistente -> 404
    resp_404 = client.get("/api/v1/loyalty/public-card/CODIGO_INEXISTENTE_999")
    assert resp_404.status_code == 404


def test_send_vip_card_email_route(client: TestClient):
    clinic_id = uuid4()
    prof_id = uuid4()
    patient_id = uuid4()
    unique_code = f"MAIL-{uuid4().hex[:6].upper()}"

    with unsafe_session_without_tenant("setup send email test") as session:
        clinic = Clinic(id=clinic_id, name="Clínica Estética Prime")
        session.add(clinic)
        session.flush()

        user = User(
            id=prof_id,
            clinic_id=clinic_id,
            name="Dra. Cristina Prime",
            email=f"cristina_{prof_id.hex[:6]}@example.com",
            role="admin",
            is_active=True,
        )
        session.add(user)
        session.flush()

        prof = Professional(
            id=prof_id,
            user_id=prof_id,
            clinic_id=clinic_id,
            name="Dra. Cristina",
            timezone="America/Sao_Paulo",
            is_active=True,
        )
        session.add(prof)
        session.flush()

        p = Patient(
            id=patient_id,
            professional_id=prof_id,
            name="Juliana Cardoso",
            phone="+5511999997777",
            email="juliana.cardoso@example.com",
            referral_code=unique_code,
            loyalty_points=50,
            vip_tier="BRONZE",
            is_active=True,
            consent_whatsapp=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(p)
        session.flush()

    app.dependency_overrides[deps.get_current_professional_id] = lambda: prof_id

    try:
        resp = client.post(f"/api/v1/loyalty/patients/{patient_id}/send-card-email")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert "juliana.cardoso@example.com" in data["recipient_email"]
    finally:
        app.dependency_overrides.pop(deps.get_current_professional_id, None)
