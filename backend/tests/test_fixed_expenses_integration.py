"""Teste de integração REAL contra o Postgres do Docker (não mockado).

T-021a/T-021b (MVP v7.1 §12.5) — despesas fixas do tenant. Mesmo padrão
de tests/test_sales_integration.py: TestClient direto contra a app,
sem mock de sessão, cada teste cria seus próprios dados via API.
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
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestCrudDespesasFixas:
    def test_criar_e_listar(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        label = f"Aluguel da sala {uuid.uuid4()}"
        resp = client.post(
            "/api/v1/fixed-expenses",
            json={"label": label, "amount": "800.00", "category": "aluguel"},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["label"] == label
        assert body["amount"] == "800.00"
        assert body["periodicity"] == "MONTHLY"
        assert body["active_to"] is None

        resp = client.get("/api/v1/fixed-expenses", headers=auth_headers)
        assert resp.status_code == 200
        assert any(e["label"] == label for e in resp.json())

    def test_periodicity_yearly_persiste(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            "/api/v1/fixed-expenses",
            json={
                "label": f"Taxa vigilância sanitária {uuid.uuid4()}",
                "amount": "1200.00",
                "periodicity": "YEARLY",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["periodicity"] == "YEARLY"

    def test_update_altera_valor(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create = client.post(
            "/api/v1/fixed-expenses",
            json={"label": "Água", "amount": "100.00"},
            headers=auth_headers,
        )
        expense_id = create.json()["id"]

        resp = client.patch(
            f"/api/v1/fixed-expenses/{expense_id}",
            json={"amount": "120.00"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == "120.00"

    def test_archive_fecha_active_to_e_some_da_listagem_ativa(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create = client.post(
            "/api/v1/fixed-expenses",
            json={"label": f"Descarte de lixo {uuid.uuid4()}", "amount": "50.00"},
            headers=auth_headers,
        )
        expense_id = create.json()["id"]

        resp = client.delete(f"/api/v1/fixed-expenses/{expense_id}", headers=auth_headers)
        assert resp.status_code == 204

        active = client.get("/api/v1/fixed-expenses", headers=auth_headers)
        assert not any(e["id"] == expense_id for e in active.json())

        all_expenses = client.get(
            "/api/v1/fixed-expenses", params={"include_archived": True}, headers=auth_headers
        )
        archived = next(e for e in all_expenses.json() if e["id"] == expense_id)
        assert archived["active_to"] is not None

        # Nunca hard delete — a linha continua existindo via GET direto.
        direct = client.get(f"/api/v1/fixed-expenses/{expense_id}", headers=auth_headers)
        assert direct.status_code == 200

    def test_expense_inexistente_retorna_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            f"/api/v1/fixed-expenses/{uuid.uuid4()}", headers=auth_headers
        )
        assert resp.status_code == 404
