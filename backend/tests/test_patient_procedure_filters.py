"""Teste de integração REAL contra o Postgres do Docker (não mockado).

Filtros novos de E1 (pacientes: gender, has_upcoming_booking,
has_completed_treatment) e E2 (procedimentos: is_invasive,
session_plan) — ver docs/pending/BACKLOG_FILTROS_E_LAYOUT.md.
Mesmo padrão de fixtures de tests/test_procedure_ranking_integration.py.
"""

import uuid
from datetime import UTC, datetime, timedelta

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


def _create_patient(
    client: TestClient, headers: dict[str, str], name: str, gender: str | None = None
) -> str:
    payload: dict = {"name": name}
    if gender is not None:
        payload["gender"] = gender
    resp = client.post("/api/v1/patients", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_procedure(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    is_invasive: bool | None = None,
    session_plan: str | None = None,
) -> str:
    payload: dict = {"name": name, "price": "100.00", "estimated_cost": "30.00"}
    if is_invasive is not None:
        payload["is_invasive"] = is_invasive
    if session_plan is not None:
        payload["session_plan"] = session_plan
    resp = client.post("/api/v1/procedures", json=payload, headers=headers)
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


class TestFiltroGenero:
    def test_criar_paciente_com_genero_e_recuperar(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        patient_id = _create_patient(
            client, auth_headers, f"Paciente Genero {uuid.uuid4()}", gender="FEMALE"
        )
        resp = client.get(f"/api/v1/patients/{patient_id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["gender"] == "FEMALE"

    def test_filtro_gender_so_retorna_pacientes_daquele_genero(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        male_id = _create_patient(client, auth_headers, f"Paciente M {marker}", gender="MALE")
        female_id = _create_patient(client, auth_headers, f"Paciente F {marker}", gender="FEMALE")

        resp = client.get(
            "/api/v1/patients",
            params={"search": marker, "gender": "MALE"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        ids = {p["id"] for p in resp.json()["items"]}
        assert male_id in ids
        assert female_id not in ids

    def test_paciente_sem_genero_definido_nao_aparece_em_filtro_algum(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        patient_id = _create_patient(client, auth_headers, f"Paciente Sem Genero {uuid.uuid4()}")
        resp = client.get(f"/api/v1/patients/{patient_id}", headers=auth_headers)
        assert resp.json()["gender"] is None

        resp = client.get(
            "/api/v1/patients",
            params={"gender": "FEMALE", "page_size": 200},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id not in ids


class TestFiltroJaTratou:
    def test_paciente_sem_venda_nem_sessao_nao_conta_como_ja_tratou(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        patient_id = _create_patient(client, auth_headers, f"Nunca Tratou {uuid.uuid4()}")

        resp = client.get(
            "/api/v1/patients",
            params={"has_completed_treatment": "true", "page_size": 200},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id not in ids

        resp = client.get(
            "/api/v1/patients",
            params={"has_completed_treatment": "false", "page_size": 200},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id in ids

    def test_venda_sem_sessao_completed_ja_conta_como_tratou_produto_revendido(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Decisão E1: Sale sozinha (produto revendido, sem sessão) conta
        como "já tratou" — não precisa esperar Session COMPLETED."""
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Comprou Produto {marker}")
        procedure_id = _create_procedure(client, auth_headers, f"Produto {uuid.uuid4()}")
        client.post("/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers)

        # Busca combinada com o filtro isola o resultado do volume
        # acumulado de outras execuções de teste (não confiar em
        # page_size cobrir "todos" os pacientes do tenant).
        resp = client.get(
            "/api/v1/patients",
            params={"search": f"Comprou Produto {marker}", "has_completed_treatment": "true"},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id in ids

    def test_sessao_completed_conta_como_ja_tratou(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Sessao Completa {marker}")
        procedure_id = _create_procedure(client, auth_headers, f"Servico {uuid.uuid4()}")
        sale_resp = client.post(
            "/api/v1/sales", json=_sale_body(patient_id, procedure_id), headers=auth_headers
        )
        session_id = sale_resp.json()["sessions"][0]["id"]
        client.patch(
            f"/api/v1/sessions/{session_id}", json={"status": "COMPLETED"}, headers=auth_headers
        )

        resp = client.get(
            "/api/v1/patients",
            params={"search": f"Sessao Completa {marker}", "has_completed_treatment": "true"},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id in ids


class TestFiltroTemAgendamento:
    def test_paciente_sem_nada_agendado_nao_conta_como_tem_agendamento(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        patient_id = _create_patient(client, auth_headers, f"Sem Agenda {marker}")

        resp = client.get(
            "/api/v1/patients",
            params={"search": f"Sem Agenda {marker}", "has_upcoming_booking": "false"},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id in ids

        resp = client.get(
            "/api/v1/patients",
            params={"search": f"Sem Agenda {marker}", "has_upcoming_booking": "true"},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id not in ids

    def test_booking_futuro_conta_como_tem_agendamento(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Decisão E1: Booking futuro ainda não convertido conta como
        "tem agendamento", mesmo sem venda associada."""
        patient_id = _create_patient(client, auth_headers, f"Com Booking {uuid.uuid4()}")
        future = (datetime.now(UTC) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
        resp = client.post(
            "/api/v1/bookings",
            json={"patient_id": patient_id, "scheduled_at": future, "modality": "IN_PERSON"},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

        resp = client.get(
            "/api/v1/patients",
            params={"has_upcoming_booking": "true", "page_size": 200},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert patient_id in ids


class TestFiltroInvasivo:
    def test_filtro_is_invasive_true_so_retorna_invasivos(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        invasive_id = _create_procedure(
            client, auth_headers, f"Preenchimento {marker}", is_invasive=True
        )
        non_invasive_id = _create_procedure(
            client, auth_headers, f"Limpeza {marker}", is_invasive=False
        )

        resp = client.get(
            "/api/v1/procedures",
            params={"is_invasive": "true", "page_size": 200},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert invasive_id in ids
        assert non_invasive_id not in ids

    def test_default_is_invasive_false_quando_nao_informado(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        procedure_id = _create_procedure(client, auth_headers, f"Sem Campo {uuid.uuid4()}")
        resp = client.get(f"/api/v1/procedures/{procedure_id}", headers=auth_headers)
        assert resp.json()["is_invasive"] is False


class TestFiltroSessionPlan:
    def test_filtro_session_plan_multiple_so_retorna_multiplas_sessoes(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        multiple_id = _create_procedure(
            client, auth_headers, f"Depilacao a Laser {marker}", session_plan="MULTIPLE"
        )
        single_id = _create_procedure(
            client, auth_headers, f"Botox {marker}", session_plan="SINGLE"
        )

        resp = client.get(
            "/api/v1/procedures",
            params={"session_plan": "MULTIPLE", "page_size": 200},
            headers=auth_headers,
        )
        ids = {p["id"] for p in resp.json()["items"]}
        assert multiple_id in ids
        assert single_id not in ids

    def test_default_session_plan_single_quando_nao_informado(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        procedure_id = _create_procedure(client, auth_headers, f"Padrao {uuid.uuid4()}")
        resp = client.get(f"/api/v1/procedures/{procedure_id}", headers=auth_headers)
        assert resp.json()["session_plan"] == "SINGLE"
