"""Testes de integração para o Sistema de Anamnese Digital (AN-07)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestAnamnesisTemplateAndQuestions:
    def test_obter_e_atualizar_template(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        # Obter template ativo
        resp = client.get("/api/v1/anamnesis/template", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        template = resp.json()
        assert "id" in template
        assert "title" in template
        assert len(template["questions"]) >= 5

        # Atualizar template
        novo_titulo = f"Ficha Customizada {uuid.uuid4()}"
        resp_update = client.put(
            "/api/v1/anamnesis/template",
            json={
                "title": novo_titulo,
                "description": "Nova descrição explicativa",
                "auto_request_on_booking": True,
            },
            headers=auth_headers,
        )
        assert resp_update.status_code == 200
        updated = resp_update.json()
        assert updated["title"] == novo_titulo
        assert updated["description"] == "Nova descrição explicativa"

    def test_crud_perguntas_e_reordenacao(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        # Criar pergunta nova
        title = f"Possui diabetes controlada? {uuid.uuid4()}"
        resp_create = client.post(
            "/api/v1/anamnesis/questions",
            json={
                "title": title,
                "description": "Se sim, informe se faz uso de insulina",
                "field_type": "yes_no",
                "is_required": True,
                "is_risk_alert": True,
                "risk_trigger_value": "yes",
                "order_index": 99,
            },
            headers=auth_headers,
        )
        assert resp_create.status_code == 201, resp_create.text
        q = resp_create.json()
        q_id = q["id"]
        assert q["title"] == title
        assert q["is_risk_alert"] is True

        # Atualizar pergunta
        resp_patch = client.put(
            f"/api/v1/anamnesis/questions/{q_id}",
            json={"description": "Atualizado com sucesso"},
            headers=auth_headers,
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["description"] == "Atualizado com sucesso"

        # Reordenar perguntas
        resp_reorder = client.post(
            "/api/v1/anamnesis/questions/reorder",
            json={"questions": [{"question_id": q_id, "order_index": 1}]},
            headers=auth_headers,
        )
        assert resp_reorder.status_code == 200

        # Deletar pergunta criada
        resp_del = client.delete(
            f"/api/v1/anamnesis/questions/{q_id}", headers=auth_headers
        )
        assert resp_del.status_code == 204


class TestPublicAnamnesisSubmission:
    def test_fluxo_completo_com_alertas_de_risco(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        # 1. Profissional gera link/token de preenchimento
        patient_name = f"Paciente Teste {uuid.uuid4()}"
        resp_token = client.post(
            "/api/v1/anamnesis/submissions/token",
            params={"patient_name": patient_name, "patient_phone": "11999998888"},
            headers=auth_headers,
        )
        assert resp_token.status_code == 200, resp_token.text
        token_data = resp_token.json()
        token = token_data["public_token"]
        assert token

        # 2. Paciente acessa tela pública sem login
        resp_form = client.get(f"/api/v1/public/anamnesis/{token}")
        assert resp_form.status_code == 200, resp_form.text
        form_data = resp_form.json()
        assert form_data["patient_name"] == patient_name
        assert form_data["is_submitted"] is False
        questions = form_data["questions"]
        assert len(questions) > 0

        # Identifica pergunta com alerta de risco (ex: gestante)
        risk_q = next((q for q in questions if q["is_risk_alert"]), questions[0])

        # 3. Paciente submete respostas
        answers = {q["id"]: "não" for q in questions}
        # Dispara o gatilho de risco
        answers[risk_q["id"]] = "yes"
        # Pergunta obrigatória de texto preenchida
        for q in questions:
            if q["field_type"] in ("text", "long_text"):
                answers[q["id"]] = "Tratamento facial preventivo"

        resp_submit = client.post(
            f"/api/v1/public/anamnesis/{token}",
            json={
                "patient_name": patient_name,
                "patient_phone": "11999998888",
                "answers": answers,
                "signature_name": "Maria Teste Silva",
                "signature_image": "data:image/png;base64,assinado",
                "tcle_accepted": True,
            },
        )
        assert resp_submit.status_code == 200, resp_submit.text
        sub_result = resp_submit.json()
        assert sub_result["submitted_at"] is not None
        assert sub_result["signature_name"] == "Maria Teste Silva"
        assert sub_result["signature_image"] == "data:image/png;base64,assinado"
        assert sub_result["tcle_accepted"] is True
        assert sub_result["tcle_accepted_at"] is not None
        assert sub_result["has_risk_alerts"] is True
        assert len(sub_result["risk_alerts_summary"]) > 0

        # 4. Profissional visualiza nas submissões recentes
        resp_list = client.get("/api/v1/anamnesis/submissions", headers=auth_headers)
        assert resp_list.status_code == 200
        submissions = resp_list.json()
        matching = [s for s in submissions if s["public_token"] == token]
        assert len(matching) == 1
        assert matching[0]["has_risk_alerts"] is True

    def test_validacao_pergunta_obrigatoria(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp_token = client.post(
            "/api/v1/anamnesis/submissions/token",
            params={"patient_name": "Maria Incompleta"},
            headers=auth_headers,
        )
        token = resp_token.json()["public_token"]

        # Submete sem nenhuma resposta (respostas vazias)
        resp_submit = client.post(
            f"/api/v1/public/anamnesis/{token}",
            json={
                "patient_name": "Maria Incompleta",
                "answers": {},
            },
        )
        # Deve falhar com 422 apontando campo obrigatório
        assert resp_submit.status_code == 422
        assert "obrigatória" in resp_submit.json()["detail"].lower()

    def test_validacao_tcle_obrigatorio(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp_token = client.post(
            "/api/v1/anamnesis/submissions/token",
            params={"patient_name": "Maria Sem TCLE"},
            headers=auth_headers,
        )
        token = resp_token.json()["public_token"]

        resp_form = client.get(f"/api/v1/public/anamnesis/{token}")
        questions = resp_form.json()["questions"]
        answers = {q["id"]: "não" for q in questions}
        for q in questions:
            if q["field_type"] in ("text", "long_text"):
                answers[q["id"]] = "Avaliação"

        # Tenta submeter com tcle_accepted: False
        resp_submit = client.post(
            f"/api/v1/public/anamnesis/{token}",
            json={
                "patient_name": "Maria Sem TCLE",
                "answers": answers,
                "tcle_accepted": False,
            },
        )
        assert resp_submit.status_code == 422
        assert "termo de consentimento" in resp_submit.json()["detail"].lower()
