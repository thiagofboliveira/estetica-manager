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


class TestBreakevenNoDashboard:
    """Épico C — "Ponto de equilíbrio do mês" (roadmap 2026-09-02)."""

    def test_this_month_traz_breakeven_remaining_amount(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "breakeven_remaining_amount" in body
        assert "breakeven_remaining_sessions_estimate" in body
        assert "breakeven_alert" in body

    def test_today_nao_traz_breakeven(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/dashboard", params={"period": "today"}, headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["breakeven_remaining_amount"] is None
        assert body["breakeven_remaining_sessions_estimate"] is None
        assert body["breakeven_alert"] is False


class TestReceivablesRespeitaAntecipacaoCongelada:
    """OBS-BACK-S3-01 (bugs.md) — is_anticipated na projeção de
    recebíveis não podia ficar hardcoded em False: uma venda feita
    com anticipates_all=True precisa projetar em D+2, não D+30*N.

    O valor usado é o congelado no snapshot_payload da venda (I3), não
    a config atual de financial_settings — por isso o teste desliga a
    antecipação de volta ANTES de ler a projeção, provando que o
    resultado reflete o que valia no momento da venda."""

    def test_venda_antecipada_cai_no_mes_da_venda_mesmo_apos_desligar_configuracao(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        patient_id: str,
        procedure_id: str,
    ) -> None:
        original = client.get(
            "/api/v1/financial-settings", headers=auth_headers
        ).json()

        patch = client.patch(
            "/api/v1/financial-settings",
            json={
                "anticipates_all": True,
                "anticipation_rate_per_installment": "1.50",
            },
            headers=auth_headers,
        )
        assert patch.status_code == 200, patch.text

        try:
            sale = client.post(
                "/api/v1/sales",
                json={
                    "patient_id": patient_id,
                    "type": "SINGLE",
                    "items": [{"procedure_id": procedure_id, "quantity": 1}],
                    "payment_method": "CREDIT",
                    "installments": 3,
                },
                headers=auth_headers,
            )
            assert sale.status_code == 201, sale.text
        finally:
            # Desliga a antecipação de volta ANTES de ler a projeção —
            # se o código lesse a config atual em vez do congelado na
            # venda, este teste pegaria a regressão.
            client.patch(
                "/api/v1/financial-settings",
                json={
                    "anticipates_all": bool(original.get("anticipates_all", False)),
                    "anticipation_rate_per_installment": original.get(
                        "anticipation_rate_per_installment"
                    ),
                },
                headers=auth_headers,
            )

        projection = client.get(
            "/api/v1/dashboard/receivables",
            params={"months_ahead": 4},
            headers=auth_headers,
        )
        assert projection.status_code == 200, projection.text
        months = projection.json()["months"]
        current_month, later_months = months[0], months[1:]

        # Com is_anticipated respeitado: a venda cai inteira em D+2, no
        # mês corrente. Sem a correção (is_anticipated hardcoded em
        # False), 3 parcelas seriam espalhadas em D+30/60/90 — o mês
        # corrente ficaria sem essa parcela e os 3 meses seguintes
        # teriam 1 parcela cada.
        assert current_month["installment_count"] >= 1
        assert all(m["installment_count"] == 0 for m in later_months)
