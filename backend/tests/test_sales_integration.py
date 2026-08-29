"""Teste de integração REAL contra o Postgres do Docker (não mockado).

Cobre o mais importante de testar de verdade (ver instrução da task):
idempotência do POST /sales. Requer:
  - ENV=development, DEV_AUTH_SECRET setado (ver .env)
  - Postgres real rodando em DATABASE_URL (docker-compose.dev.yml)
  - migrations 0001+0002 aplicadas

Roda via TestClient (fastapi.testclient / httpx) direto contra a app —
sem mock de sessão, sem fixture de transação isolada: cada teste cria
seus próprios dados (paciente/procedimento) via API para não colidir
com estado de outros testes, e não faz cleanup (ambiente de dev
descartável). Pular explicitamente se DEV_AUTH_SECRET não estiver
configurado (é assim que /dev/login se autoriza a existir).
"""

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
def token(client: TestClient) -> str:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/patients",
        json={"name": f"Paciente Teste {uuid.uuid4()}"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.fixture
def procedure_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/procedures",
        json={
            "name": f"Procedimento Teste {uuid.uuid4()}",
            "price": "1000.00",
            "estimated_cost": "300.00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _sale_body(patient_id: str, procedure_id: str, quantity: int = 1) -> dict:
    return {
        "patient_id": patient_id,
        "type": "SINGLE",
        "items": [{"procedure_id": procedure_id, "quantity": quantity}],
        "payment_method": "PIX",
        "installments": 1,
    }


class TestIdempotenciaPostSales:
    """T-015a, contrato C-1: mesma Idempotency-Key + mesmo corpo em 24h
    -> MESMA venda, 200, nunca duplicata."""

    def test_dupla_chamada_mesma_chave_nao_duplica(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        key = f"idem-{uuid.uuid4()}"
        body = _sale_body(patient_id, procedure_id)

        r1 = client.post(
            "/api/v1/sales",
            json=body,
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert r1.status_code == 201, r1.text
        sale_id_1 = r1.json()["id"]

        r2 = client.post(
            "/api/v1/sales",
            json=body,
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert r2.status_code == 200, r2.text
        sale_id_2 = r2.json()["id"]

        assert sale_id_1 == sale_id_2, "chave idêntica gerou venda diferente"
        assert r1.json()["net_profit"] == r2.json()["net_profit"]

    def test_chave_diferente_mesmo_corpo_cria_venda_nova(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        body = _sale_body(patient_id, procedure_id)

        r1 = client.post(
            "/api/v1/sales",
            json=body,
            headers={**auth_headers, "Idempotency-Key": f"a-{uuid.uuid4()}"},
        )
        r2 = client.post(
            "/api/v1/sales",
            json=body,
            headers={**auth_headers, "Idempotency-Key": f"b-{uuid.uuid4()}"},
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]

    def test_mesma_chave_corpo_diferente_e_conflito(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        key = f"conflict-{uuid.uuid4()}"
        r1 = client.post(
            "/api/v1/sales",
            json=_sale_body(patient_id, procedure_id, quantity=1),
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert r1.status_code == 201

        r2 = client.post(
            "/api/v1/sales",
            json=_sale_body(patient_id, procedure_id, quantity=2),
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert r2.status_code == 409

    def test_sem_chave_cada_post_cria_venda_nova(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        body = _sale_body(patient_id, procedure_id)
        r1 = client.post("/api/v1/sales", json=body, headers=auth_headers)
        r2 = client.post("/api/v1/sales", json=body, headers=auth_headers)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]


class TestVendaGeraSessoes:
    def test_avulso_gera_uma_sessao_scheduled(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        resp = client.post(
            "/api/v1/sales",
            json=_sale_body(patient_id, procedure_id),
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        sessions = resp.json()["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["status"] == "SCHEDULED"

    def test_pacote_gera_n_sessoes_pending(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        body = {
            "patient_id": patient_id,
            "type": "PACKAGE",
            "items": [{"procedure_id": procedure_id, "quantity": 5}],
            "payment_method": "PIX",
            "installments": 1,
        }
        resp = client.post("/api/v1/sales", json=body, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        sessions = resp.json()["sessions"]
        assert len(sessions) == 5
        assert all(s["status"] == "PENDING" for s in sessions)


class TestValidacaoDeVenda:
    def test_paciente_inexistente_retorna_404(
        self, client: TestClient, auth_headers: dict[str, str], procedure_id: str
    ) -> None:
        body = _sale_body(str(uuid.uuid4()), procedure_id)
        resp = client.post("/api/v1/sales", json=body, headers=auth_headers)
        assert resp.status_code == 404

    def test_procedimento_inexistente_retorna_404(
        self, client: TestClient, auth_headers: dict[str, str], patient_id: str
    ) -> None:
        body = _sale_body(patient_id, str(uuid.uuid4()))
        resp = client.post("/api/v1/sales", json=body, headers=auth_headers)
        assert resp.status_code == 404
