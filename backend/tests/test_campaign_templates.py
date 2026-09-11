from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.campaign import CampaignTemplate
from app.repositories.campaign import CampaignTemplateRepository
from app.schemas.campaign import CampaignTemplateCreate, CampaignTemplateUpdate
from app.services.campaign_service import (
    CampaignService,
    CampaignTemplateNotFoundError,
    SYSTEM_TEMPLATES,
)


@pytest.fixture
def mock_repo():
    return MagicMock(spec=CampaignTemplateRepository)


def test_list_templates_combines_db_and_system(mock_repo):
    prof_id = uuid4()
    custom_template = CampaignTemplate(
        id=uuid4(),
        professional_id=prof_id,
        clinic_id=None,
        title="Promoção de Verão ☀️",
        category="promos",
        description="Campanha para janeiro",
        message_text="Oi {nome}! Temos uma oferta especial de verão para você!",
        is_active=True,
    )
    mock_repo.list_templates.return_value = [custom_template]

    svc = CampaignService(repo=mock_repo)
    results = svc.list_templates()

    # Deve conter o customizado e os templates de sistema
    assert len(results) == 1 + len(SYSTEM_TEMPLATES)
    assert results[0].title == "Promoção de Verão ☀️"
    assert results[0].is_system is False

    system_items = [r for r in results if r.is_system]
    assert len(system_items) == len(SYSTEM_TEMPLATES)
    assert any(s.title == "💉 Botox Day Especial" for s in system_items)


def test_list_templates_filters_by_category(mock_repo):
    prof_id = uuid4()
    custom_promo = CampaignTemplate(
        id=uuid4(),
        professional_id=prof_id,
        clinic_id=None,
        title="Drenagem Linfática Combo",
        category="promos",
        description="Pacote 5 sessões",
        message_text="Oi {nome}! Pacote de drenagem...",
        is_active=True,
    )
    mock_repo.list_templates.return_value = [custom_promo]

    svc = CampaignService(repo=mock_repo)
    results = svc.list_templates(category="promos")

    mock_repo.list_templates.assert_called_once_with(category="promos")
    assert all(r.category == "promos" for r in results)


def test_create_custom_template(mock_repo):
    prof_id = uuid4()
    clinic_id = uuid4()
    created_id = uuid4()

    def fake_add(tpl):
        tpl.id = created_id
        tpl.professional_id = prof_id
        tpl.created_at = None
        tpl.updated_at = None
        return tpl

    mock_repo.add.side_effect = fake_add

    svc = CampaignService(repo=mock_repo)
    payload = CampaignTemplateCreate(
        title="Peeling de Diamante VIP",
        category="promos",
        description="Oferta exclusiva",
        message_text="Oi {nome}, agende seu peeling com desconto especial!",
    )

    out = svc.create_template(payload, clinic_id=clinic_id)

    assert out.id == created_id
    assert out.title == "Peeling de Diamante VIP"
    assert out.category == "promos"
    assert out.clinic_id == clinic_id
    assert out.is_system is False
    mock_repo.add.assert_called_once()


def test_update_custom_template(mock_repo):
    tpl_id = uuid4()
    prof_id = uuid4()
    existing = CampaignTemplate(
        id=tpl_id,
        professional_id=prof_id,
        clinic_id=None,
        title="Título Antigo",
        category="promos",
        description="Desc antiga",
        message_text="Texto antigo {nome}",
        is_active=True,
    )
    mock_repo.get.return_value = existing

    svc = CampaignService(repo=mock_repo)
    payload = CampaignTemplateUpdate(
        title="Título Atualizado ✨",
        message_text="Novo texto {nome}!",
    )

    out = svc.update_template(tpl_id, payload)

    assert out.title == "Título Atualizado ✨"
    assert out.message_text == "Novo texto {nome}!"
    assert out.category == "promos"  # manteve
    mock_repo.flush.assert_called_once()


def test_update_template_not_found(mock_repo):
    mock_repo.get.return_value = None
    svc = CampaignService(repo=mock_repo)

    with pytest.raises(CampaignTemplateNotFoundError):
        svc.update_template(uuid4(), CampaignTemplateUpdate(title="Inexistente"))


def test_delete_custom_template(mock_repo):
    tpl_id = uuid4()
    prof_id = uuid4()
    existing = CampaignTemplate(
        id=tpl_id,
        professional_id=prof_id,
        clinic_id=None,
        title="Para Deletar",
        category="promos",
        description=None,
        message_text="Texto",
        is_active=True,
    )
    mock_repo.get.return_value = existing

    svc = CampaignService(repo=mock_repo)
    svc.delete_template(tpl_id)

    mock_repo.delete.assert_called_once_with(existing)
    mock_repo.flush.assert_called_once()


def test_delete_template_not_found(mock_repo):
    mock_repo.get.return_value = None
    svc = CampaignService(repo=mock_repo)

    with pytest.raises(CampaignTemplateNotFoundError):
        svc.delete_template(uuid4())


class TestCampaignTemplatesApi:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        resp = client.post("/dev/login")
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def test_api_list_and_crud(self, client, auth_headers):
        # 1. Listagem inicial contém templates padrão
        resp = client.get("/api/v1/campaigns/templates", headers=auth_headers)
        assert resp.status_code == 200
        initial_templates = resp.json()
        assert len(initial_templates) >= 6
        assert any(t["is_system"] for t in initial_templates)

        # 2. Criação de template customizado
        unique_title = f"Harmonização VIP {uuid4()}"
        create_payload = {
            "title": unique_title,
            "category": "promos",
            "description": "Campanha exclusiva para pacientes fiéis",
            "message_text": "Oi {nome}! Temos condições exclusivas para harmonização este mês!",
        }
        resp = client.post("/api/v1/campaigns/templates", json=create_payload, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        created = resp.json()
        assert created["title"] == unique_title
        assert created["is_system"] is False
        template_id = created["id"]

        # 3. Listagem deve conter o novo modelo
        resp = client.get("/api/v1/campaigns/templates", headers=auth_headers)
        assert resp.status_code == 200
        assert any(t["id"] == template_id for t in resp.json())

        # 4. Atualização do template
        update_payload = {
            "title": f"{unique_title} [Atualizado]",
            "message_text": "Oi {nome}! Mensagem com texto atualizado!",
        }
        resp = client.put(f"/api/v1/campaigns/templates/{template_id}", json=update_payload, headers=auth_headers)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["title"] == f"{unique_title} [Atualizado]"
        assert updated["message_text"] == "Oi {nome}! Mensagem com texto atualizado!"

        # 5. Deleção do template
        resp = client.delete(f"/api/v1/campaigns/templates/{template_id}", headers=auth_headers)
        assert resp.status_code == 204

        # 6. Não deve mais aparecer
        resp = client.get("/api/v1/campaigns/templates", headers=auth_headers)
        assert resp.status_code == 200
        assert not any(t["id"] == template_id for t in resp.json())

