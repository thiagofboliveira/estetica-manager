from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.db.session import unsafe_session_without_tenant
from app.main import app
from app.models.clinic import Clinic
from app.models.loyalty import LoyaltyReward
from app.models.patient import Patient
from app.models.professional import Professional
from app.models.user import User


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_loyalty_rewards_crud_and_public_card_reflection(client: TestClient):
    clinic_id = uuid4()
    prof_id = uuid4()
    patient_id = uuid4()
    referral_code = f"VIP-{uuid4().hex[:6].upper()}"

    with unsafe_session_without_tenant("setup loyalty rewards test") as session:
        clinic = Clinic(id=clinic_id, name="Clínica Glow VIP")
        session.add(clinic)
        session.flush()

        user = User(
            id=prof_id,
            clinic_id=clinic_id,
            name="Dra. Roberta Glow",
            email=f"roberta_{prof_id.hex[:6]}@example.com",
            role="admin",
            is_active=True,
        )
        session.add(user)
        session.flush()

        prof = Professional(
            id=prof_id,
            user_id=prof_id,
            clinic_id=clinic_id,
            name="Dra. Roberta",
            slug=f"dra-roberta-{prof_id.hex[:4]}",
            timezone="America/Sao_Paulo",
            is_active=True,
        )
        session.add(prof)
        session.flush()

        p = Patient(
            id=patient_id,
            professional_id=prof_id,
            name="Camila Queiroz",
            phone="+5511988887777",
            email="camila.queiroz@example.com",
            referral_code=referral_code,
            loyalty_points=150,
            vip_tier="SILVER",
            is_active=True,
            consent_whatsapp=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(p)
        session.flush()

    app.dependency_overrides[deps.get_current_professional_id] = lambda: prof_id

    try:
        # 1. Lista inicial vazia
        resp = client.get("/api/v1/loyalty/rewards")
        assert resp.status_code == 200
        assert resp.json() == []

        # 2. Quando não há recompensas customizadas, o Cartão VIP público exibe as padrões de mercado
        resp_pub = client.get(f"/api/v1/loyalty/public-card/{referral_code}")
        assert resp_pub.status_code == 200
        data_pub = resp_pub.json()
        assert len(data_pub["catalog_rewards"]) == 4
        assert data_pub["catalog_rewards"][0]["title"] == "R$ 25 de Desconto"

        # 3. Criar recompensa 1 (Ativa)
        payload1 = {
            "points_cost": 80,
            "title": "Revitalização Labial HidraGloss",
            "description": "Hidratação profunda e efeito gloss nos lábios.",
            "discount_value": 75.0,
            "is_active": True,
            "order_index": 1,
        }
        resp1 = client.post("/api/v1/loyalty/rewards", json=payload1)
        assert resp1.status_code == 201, resp1.text
        r1_data = resp1.json()
        assert r1_data["title"] == "Revitalização Labial HidraGloss"
        assert r1_data["points_cost"] == 80
        r1_id = r1_data["id"]

        # 4. Criar recompensa 2 (Inativa)
        payload2 = {
            "points_cost": 150,
            "title": "Sessão de Radiofrequência",
            "description": "Estímulo de colágeno facial.",
            "discount_value": 150.0,
            "is_active": False,
            "order_index": 2,
        }
        resp2 = client.post("/api/v1/loyalty/rewards", json=payload2)
        assert resp2.status_code == 201
        r2_id = resp2.json()["id"]

        # 5. Listar todas vs apenas ativas
        all_rewards = client.get("/api/v1/loyalty/rewards").json()
        assert len(all_rewards) == 2

        active_rewards = client.get("/api/v1/loyalty/rewards?active_only=true").json()
        assert len(active_rewards) == 1
        assert active_rewards[0]["id"] == r1_id

        # 6. O Cartão VIP público agora deve exibir as recompensas customizadas da profissional (apenas ativas)
        resp_pub2 = client.get(f"/api/v1/loyalty/public-card/{referral_code}")
        assert resp_pub2.status_code == 200
        data_pub2 = resp_pub2.json()
        assert len(data_pub2["catalog_rewards"]) == 1
        assert data_pub2["catalog_rewards"][0]["title"] == "Revitalização Labial HidraGloss"
        assert data_pub2["catalog_rewards"][0]["points_cost"] == 80

        # 7. Atualizar recompensa 2 tornando-a ativa e mudando o título
        update_payload = {
            "title": "Radiofrequência Facial Completa",
            "is_active": True,
        }
        resp_update = client.put(f"/api/v1/loyalty/rewards/{r2_id}", json=update_payload)
        assert resp_update.status_code == 200
        assert resp_update.json()["title"] == "Radiofrequência Facial Completa"
        assert resp_update.json()["is_active"] is True

        # Agora o cartão público tem 2 recompensas
        resp_pub3 = client.get(f"/api/v1/loyalty/public-card/{referral_code}")
        assert len(resp_pub3.json()["catalog_rewards"]) == 2

        # 8. Deletar recompensa 1
        resp_del = client.delete(f"/api/v1/loyalty/rewards/{r1_id}")
        assert resp_del.status_code == 204

        remaining = client.get("/api/v1/loyalty/rewards").json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == r2_id

    finally:
        app.dependency_overrides.pop(deps.get_current_professional_id, None)
