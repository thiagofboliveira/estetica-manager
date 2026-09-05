"""Teste de integração REAL contra o Postgres do Docker (não mockado).

G-13 — eventos de ativação. Antes desta task não havia nenhuma tabela
de eventos, funil ou cohort (L-4, docs/README.md). Cobre o mínimo já
conectado: first_procedure_created, first_sale_recorded,
first_patient_imported — idempotentes (disparam só na 1ª ocorrência).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import _decode
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
def professional_id(auth_headers: dict[str, str]) -> str:
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    return _decode(token)["sub"]


def _event_count(name: str, professional_id: str) -> int:
    """RLS de `events` exige o GUC de tenant setado na conexão (I2) — a
    mesma exigência já vista em test_retention_reengagement.py para
    UPDATE direto no Postgres fora do fluxo normal da API."""
    from sqlalchemy import text

    from app.db.session import unsafe_session_without_tenant

    with unsafe_session_without_tenant("test: contar eventos") as session:
        session.execute(
            text("SELECT set_config('app.professional_id', :pid, true)"),
            {"pid": professional_id},
        )
        return session.execute(
            text("SELECT count(*) FROM events WHERE name = :name"), {"name": name}
        ).scalar_one()


class TestIdempotenciaDeEventos:
    def test_dois_procedimentos_geram_no_maximo_um_evento_first(
        self, client: TestClient, auth_headers: dict[str, str], professional_id: str
    ) -> None:
        before = _event_count("first_procedure_created", professional_id)

        for _ in range(2):
            resp = client.post(
                "/api/v1/procedures",
                json={
                    "name": f"Idempotencia Proc {uuid.uuid4()}",
                    "price": "100.00",
                    "estimated_cost": "30.00",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 201, resp.text

        after = _event_count("first_procedure_created", professional_id)
        # Se o evento nunca existiu antes, cria exatamente 1. Se já
        # existia, permanece igual — nunca soma 2 pelas 2 chamadas.
        assert after in (before, before + 1)
        assert after >= 1

    def test_venda_criada_emite_first_sale_recorded(
        self, client: TestClient, auth_headers: dict[str, str], professional_id: str
    ) -> None:
        before = _event_count("first_sale_recorded", professional_id)

        patient_resp = client.post(
            "/api/v1/patients",
            json={"name": f"Evento Venda {uuid.uuid4()}"},
            headers=auth_headers,
        )
        procedure_resp = client.post(
            "/api/v1/procedures",
            json={
                "name": f"Evento Venda Proc {uuid.uuid4()}",
                "price": "100.00",
                "estimated_cost": "30.00",
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/sales",
            json={
                "patient_id": patient_resp.json()["id"],
                "type": "SINGLE",
                "items": [{"procedure_id": procedure_resp.json()["id"], "quantity": 1}],
                "payment_method": "PIX",
                "installments": 1,
            },
            headers=auth_headers,
        )

        after = _event_count("first_sale_recorded", professional_id)
        assert after >= max(before, 1)
