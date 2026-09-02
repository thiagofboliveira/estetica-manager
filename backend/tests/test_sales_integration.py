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

    def test_parcela_fora_da_faixa_de_payment_fee_rules_retorna_422(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        """T-024a: sem isso, a venda passaria com taxa silenciosamente
        zerada (I7) — número errado é pior que nenhum número."""
        # Faixa alta e nunca usada por outros testes/seeds compartilhando o
        # mesmo banco de dev — não confiar em "nenhuma regra CREDIT existe",
        # já que outros testes podem ter seedado 1x/2-6x/7-12x antes.
        body = _sale_body(patient_id, procedure_id)
        body["payment_method"] = "CREDIT"
        body["installments"] = 37

        resp = client.post("/api/v1/sales", json=body, headers=auth_headers)

        assert resp.status_code == 422, resp.text
        assert "regra de taxa" in resp.json()["detail"].lower()


class TestCorrecaoDeVenda:
    """T-017, A-02: venda registrada errada pode ser corrigida.

    Nunca UPDATE numa Sale já persistida (FROZEN_FIELDS) — corrigir é
    estornar (REFUNDED) + criar uma venda nova, com sale_audit ligando
    as duas."""

    def test_patch_estorna_original_e_cria_venda_nova(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        original = client.post(
            "/api/v1/sales",
            json=_sale_body(patient_id, procedure_id, quantity=1),
            headers=auth_headers,
        )
        assert original.status_code == 201, original.text
        original_id = original.json()["id"]

        corrected_body = _sale_body(patient_id, procedure_id, quantity=2)
        corrected_body["reason"] = "Quantidade errada na venda original"

        resp = client.patch(
            f"/api/v1/sales/{original_id}", json=corrected_body, headers=auth_headers
        )

        assert resp.status_code == 200, resp.text
        new_sale = resp.json()
        assert new_sale["id"] != original_id
        assert new_sale["status"] == "ACTIVE"
        assert new_sale["items"][0]["quantity"] == 2

        original_after = client.get(
            f"/api/v1/sales/{original_id}", headers=auth_headers
        )
        assert original_after.status_code == 200
        assert original_after.json()["status"] == "REFUNDED"

        # Prova real de que sale_audit foi gravado — não basta checar o
        # efeito colateral (status REFUNDED, novo id); sem isso, deletar
        # a chamada self._sale_audit.add(audit) no service não quebraria
        # nenhum teste.
        audit_resp = client.get(
            f"/api/v1/sales/{original_id}/audit", headers=auth_headers
        )
        assert audit_resp.status_code == 200, audit_resp.text
        audit_entries = audit_resp.json()
        assert len(audit_entries) == 1
        assert audit_entries[0]["original_sale_id"] == original_id
        assert audit_entries[0]["replacement_sale_id"] == new_sale["id"]
        assert audit_entries[0]["reason"] == "Quantidade errada na venda original"

    def test_patch_sem_reason_e_422(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        original = client.post(
            "/api/v1/sales",
            json=_sale_body(patient_id, procedure_id),
            headers=auth_headers,
        )
        assert original.status_code == 201, original.text

        body = _sale_body(patient_id, procedure_id)
        resp = client.patch(
            f"/api/v1/sales/{original.json()['id']}", json=body, headers=auth_headers
        )
        assert resp.status_code == 422

    def test_patch_venda_inexistente_e_404(
        self, client: TestClient, auth_headers: dict[str, str], patient_id: str, procedure_id: str
    ) -> None:
        body = _sale_body(patient_id, procedure_id)
        body["reason"] = "teste"
        resp = client.patch(
            f"/api/v1/sales/{uuid.uuid4()}", json=body, headers=auth_headers
        )
        assert resp.status_code == 404

    def test_patch_venda_ja_estornada_e_409(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        original = client.post(
            "/api/v1/sales",
            json=_sale_body(patient_id, procedure_id),
            headers=auth_headers,
        )
        original_id = original.json()["id"]

        first_correction = _sale_body(patient_id, procedure_id)
        first_correction["reason"] = "primeira correção"
        client.patch(
            f"/api/v1/sales/{original_id}",
            json=first_correction,
            headers=auth_headers,
        )

        second_correction = _sale_body(patient_id, procedure_id)
        second_correction["reason"] = "segunda correção, venda já estornada"
        resp = client.patch(
            f"/api/v1/sales/{original_id}",
            json=second_correction,
            headers=auth_headers,
        )
        assert resp.status_code == 409
