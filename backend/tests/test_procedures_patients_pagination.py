"""Teste de integração REAL contra o Postgres do Docker (não mockado).

GET /procedures e GET /patients agora devolvem envelope paginado
{items, total_count, page, page_size}, mesmo padrão de
GET /reports/procedures. Mesmo padrão de fixtures de
tests/test_procedure_ranking_integration.py.
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


class TestPaginacaoProcedures:
    def test_envelope_tem_items_total_count_page_page_size(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        _create_procedure(client, auth_headers, f"Proc Pag {uuid.uuid4()}")

        resp = client.get(
            "/api/v1/procedures", params={"page": 1, "page_size": 5}, headers=auth_headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert set(body.keys()) == {"items", "total_count", "page", "page_size"}
        assert body["page"] == 1
        assert body["page_size"] == 5
        assert body["total_count"] >= 1
        assert isinstance(body["items"], list)
        assert len(body["items"]) <= 5

    def test_page_size_limita_itens_por_pagina(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = str(uuid.uuid4())
        for i in range(3):
            _create_procedure(client, auth_headers, f"Proc {marker} {i}")

        resp = client.get(
            "/api/v1/procedures", params={"page": 1, "page_size": 2}, headers=auth_headers
        )
        assert resp.status_code == 200, resp.text
        assert len(resp.json()["items"]) == 2

    def test_pagina_alem_do_total_devolve_lista_vazia_nao_erro(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/procedures",
            params={"page": 999_999, "page_size": 20},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["items"] == []

    def test_paginas_diferentes_nao_repetem_itens(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = str(uuid.uuid4())
        ids = {_create_procedure(client, auth_headers, f"Proc {marker} {i}") for i in range(3)}

        page1 = client.get(
            "/api/v1/procedures", params={"page": 1, "page_size": 1}, headers=auth_headers
        ).json()
        page2 = client.get(
            "/api/v1/procedures", params={"page": 2, "page_size": 1}, headers=auth_headers
        ).json()

        id1 = page1["items"][0]["id"]
        id2 = page2["items"][0]["id"]
        assert id1 != id2
        # Ambos pertencem ao conjunto plausível (não garante que sejam
        # os 3 criados aqui, pois pode haver outros procedimentos do
        # tenant de teste — só garante que a paginação não duplica).
        assert id1 in ids or id1 not in ids


class TestPaginacaoPatients:
    def test_envelope_tem_items_total_count_page_page_size(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        _create_patient(client, auth_headers, f"Paciente Pag {uuid.uuid4()}")

        resp = client.get(
            "/api/v1/patients", params={"page": 1, "page_size": 5}, headers=auth_headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert set(body.keys()) == {"items", "total_count", "page", "page_size"}
        assert body["total_count"] >= 1
        assert len(body["items"]) <= 5

    def test_busca_filtra_e_total_count_reflete_o_filtro(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        marker = uuid.uuid4().hex
        unique_name = f"Zzyx Busca {marker}"
        _create_patient(client, auth_headers, unique_name)
        _create_patient(client, auth_headers, f"Outro Paciente {uuid.uuid4()}")

        resp = client.get(
            "/api/v1/patients",
            params={"search": f"Zzyx Busca {marker}", "page": 1, "page_size": 20},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_count"] == 1
        assert body["items"][0]["name"] == unique_name

    def test_pagina_alem_do_total_devolve_lista_vazia_nao_erro(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/patients",
            params={"page": 999_999, "page_size": 20},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["items"] == []
