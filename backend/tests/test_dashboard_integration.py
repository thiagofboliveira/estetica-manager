"""Teste de integração REAL contra o Postgres do Docker (não mockado).

T-022/T-022a/T-023 (MVP v6 §13) — GET /dashboard. Mesmo padrão de
tests/test_sales_integration.py.
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


class TestValidacaoDeParametros:
    def test_period_invalido_e_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "nonsense"}, headers=auth_headers
        )
        assert resp.status_code == 422

    def test_custom_sem_datas_e_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "custom"}, headers=auth_headers
        )
        assert resp.status_code == 422


class TestLucroRealDoMesSoEmFiltroMensal:
    def test_today_nao_tem_fixed_expenses_total(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "today"}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["fixed_expenses_total"] is None
        assert resp.json()["net_profit_after_fixed_expenses"] is None

    def test_this_month_tem_fixed_expenses_total(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["fixed_expenses_total"] is not None

    def test_despesa_recem_criada_aparece_no_total_mensal(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        label = f"Aluguel teste {uuid.uuid4()}"
        create = client.post(
            "/api/v1/fixed-expenses",
            json={"label": label, "amount": "800.00"},
            headers=auth_headers,
        )
        assert create.status_code == 201

        before = client.get(
            "/api/v1/dashboard", params={"period": "this_month"}, headers=auth_headers
        ).json()

        # Arquiva pra não sujar outros testes/ambiente de dev.
        client.delete(
            f"/api/v1/fixed-expenses/{create.json()['id']}", headers=auth_headers
        )

        assert float(before["fixed_expenses_total"]) >= 800.00


class TestHasAnyDataContrato:
    """T-022a, contrato C-2 — usa o professional seed padrão, que já tem
    vendas de outros testes de integração: aqui só provamos que
    has_any_data=true quando existe QUALQUER venda (não testamos o
    caso false aqui pois exigiria um tenant isolado; provado
    manualmente e coberto pela suíte pura de domínio, test_dashboard.py)."""

    def test_com_historico_e_true(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["has_any_data"] is True


class TestHasProvisionalProfitContrato:
    """T-022b, A-07: desbloqueia o badge "lucro provisório" — a
    profissional precisa saber que o lucro do mês inclui pacotes ainda
    não totalmente concluídos."""

    def test_pacote_com_sessao_pending_no_mes_e_true(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        patient = client.post(
            "/api/v1/patients",
            json={"name": f"Paciente Dashboard {uuid.uuid4()}"},
            headers=auth_headers,
        )
        assert patient.status_code == 201
        procedure = client.post(
            "/api/v1/procedures",
            json={
                "name": f"Procedimento Dashboard {uuid.uuid4()}",
                "price": "500.00",
                "estimated_cost": "100.00",
            },
            headers=auth_headers,
        )
        assert procedure.status_code == 201

        sale = client.post(
            "/api/v1/sales",
            json={
                "patient_id": patient.json()["id"],
                "type": "PACKAGE",
                "items": [{"procedure_id": procedure.json()["id"], "quantity": 3}],
                "payment_method": "PIX",
            },
            headers=auth_headers,
        )
        assert sale.status_code in (200, 201), sale.text
        # Pacote recém-vendido: todas as sessões nascem PENDING (sem
        # data), então o item nunca esgota — has_provisional_profit
        # tem que ser True para este mês.

        resp = client.get(
            "/api/v1/dashboard", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["has_provisional_profit"] is True
