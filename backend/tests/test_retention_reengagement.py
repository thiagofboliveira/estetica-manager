"""Teste de integração REAL contra o Postgres do Docker (não mockado).

E4 — "Quem chamar hoje": pacientes nunca tratados ou parados há X dias
(F4-02 a F4-04). Ver docs/pending/BACKLOG_FILTROS_E_LAYOUT.md. Mesmo
padrão de fixtures de tests/test_patient_procedure_filters.py.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.security import _decode
from app.db.session import engine
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


def _create_patient(client: TestClient, headers: dict[str, str], name: str) -> str:
    resp = client.post("/api/v1/patients", json={"name": name}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_procedure(client: TestClient, headers: dict[str, str], name: str) -> str:
    resp = client.post(
        "/api/v1/procedures",
        json={"name": name, "price": "100.00", "estimated_cost": "30.00"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _sale_body(patient_id: str, procedure_id: str) -> dict:
    return {
        "patient_id": patient_id,
        "type": "SINGLE",
        "items": [{"procedure_id": procedure_id, "quantity": 1}],
        "payment_method": "PIX",
        "installments": 1,
    }


def _complete_first_session(client: TestClient, headers: dict[str, str], sale_resp: dict) -> str:
    session_id = sale_resp["sessions"][0]["id"]
    resp = client.patch(
        f"/api/v1/sessions/{session_id}", json={"status": "COMPLETED"}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    return session_id


def _backdate_completed_at(professional_id: str, session_id: str, days_ago: int) -> None:
    """Testa "parado há X dias" sem esperar X dias de verdade — recua
    completed_at direto no Postgres (não existe campo editável via API
    para isso, é derivado do momento real da conclusão). RLS exige o GUC
    de tenant setado na própria conexão antes do UPDATE (I2)."""
    with engine.begin() as conn:
        conn.execute(
            text("SELECT set_config('app.professional_id', :pid, true)"),
            {"pid": professional_id},
        )
        conn.execute(
            text("UPDATE sessions SET completed_at = now() - (:days || ' days')::interval WHERE id = :id"),
            {"days": days_ago, "id": session_id},
        )


class TestNuncaTratados:
    def test_paciente_sem_venda_nem_sessao_aparece_em_nunca_tratados(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Nunca Tratou Reeng {marker}")

        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"page_size": 200},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        ids = {p["patient_id"] for p in resp.json()["never_treated"]}
        assert patient_id in ids

    def test_paciente_com_venda_nao_aparece_em_nunca_tratados(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Ja Comprou Reeng {marker}")
        procedure_id = _create_procedure(client, auth_headers, f"Produto Reeng {uuid.uuid4()}")
        client.post("/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers)

        resp = client.get("/api/v1/retention/reengagement", headers=auth_headers)
        ids = {p["patient_id"] for p in resp.json()["never_treated"]}
        assert patient_id not in ids


class TestInativoPorDias:
    def test_sessao_completed_ha_muito_tempo_aparece_como_inativo(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Parado Ha Muito {marker}")
        procedure_id = _create_procedure(client, auth_headers, f"Servico Antigo {uuid.uuid4()}")
        sale_resp = client.post(
            "/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers
        )
        session_id = _complete_first_session(client, auth_headers, sale_resp.json())
        token = auth_headers["Authorization"].removeprefix("Bearer ")
        professional_id = _decode(token)["sub"]
        _backdate_completed_at(professional_id, session_id, days_ago=90)

        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"inactive_days": 60, "page_size": 200},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        ids = {p["patient_id"] for p in resp.json()["inactive"]}
        assert patient_id in ids

    def test_sessao_completed_recente_nao_aparece_como_inativo(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Tratou Recente {marker}")
        procedure_id = _create_procedure(client, auth_headers, f"Servico Recente {uuid.uuid4()}")
        sale_resp = client.post(
            "/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers
        )
        _complete_first_session(client, auth_headers, sale_resp.json())

        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"inactive_days": 30},
            headers=auth_headers,
        )
        ids = {p["patient_id"] for p in resp.json()["inactive"]}
        assert patient_id not in ids

    def test_paciente_nunca_tratado_nao_aparece_em_inativos(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"So Nunca Tratou {marker}")

        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"inactive_days": 1},
            headers=auth_headers,
        )
        ids = {p["patient_id"] for p in resp.json()["inactive"]}
        assert patient_id not in ids

    def test_inactive_days_threshold_retorna_no_response(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"inactive_days": 45},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["inactive_days_threshold"] == 45

    def test_default_inactive_days_e_60(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/retention/reengagement", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["inactive_days_threshold"] == 60


class TestPaginacao:
    def test_page_size_limita_itens_por_pagina(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        for i in range(3):
            _create_patient(client, auth_headers, f"Paginacao Reeng {marker} {i}")

        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"page_size": 2},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["never_treated"]) <= 2
        assert body["page"] == 1
        assert body["page_size"] == 2

    def test_total_count_reflete_volume_real_nao_so_a_pagina(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        for i in range(3):
            _create_patient(client, auth_headers, f"Total Reeng {marker} {i}")

        resp = client.get(
            "/api/v1/retention/reengagement",
            params={"page_size": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["never_treated"]) == 1
        assert body["never_treated_total_count"] >= 3
