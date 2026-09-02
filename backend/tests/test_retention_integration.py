"""T-025..T-031, T-045/T-045a/T-045b — ciclo completo do motor de
retorno, testado contra Postgres real (mesmo padrão de
test_sales_integration.py).

Nota (Task 8): `GET`/`PATCH /api/v1/retention/opportunities` foram
implementadas nesta task (T-029/T-030) — os testes abaixo agora exercitam
o ciclo completo via HTTP (listar -> contatar -> nova venda fecha). O
teste stopgap da Task 7 (`test_close_open_opportunities_via_nova_venda_stopgap`,
que verificava o fechamento direto no banco sem depender destas rotas)
foi removido: `test_ciclo_completo_venda_completa_lista_contata_nova_venda_fecha`
abaixo cobre o mesmo caminho (fechamento automático em SaleService.create,
T-028) e também a listagem/edição via API, tornando-o redundante.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import get_tenant_session
from app.main import app
from app.models.return_opportunity import ReturnOpportunity

_DEV_PROFESSIONAL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    resp = client.post("/dev/login")
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def patient_id(client, auth_headers):
    resp = client.post(
        "/api/v1/patients",
        json={"name": "Maria Retenção", "phone": "+5511987654321"},
        headers=auth_headers,
    )
    return resp.json()["id"]


def _create_procedure(client, auth_headers, *, interval_days: int):
    resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Botox Retenção",
            "price": "1000.00",
            "estimated_cost": "100.00",
            "return_interval_days": interval_days,
        },
        headers=auth_headers,
    )
    return resp.json()["id"]


def _sell_and_complete_single(client, auth_headers, patient_id, procedure_id):
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    session_id = sale_resp.json()["sessions"][0]["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    return sale_resp.json()["id"]


def test_ciclo_completo_venda_completa_lista_contata_nova_venda_fecha(
    client, auth_headers, patient_id
):
    procedure_id = _create_procedure(client, auth_headers, interval_days=1)
    _sell_and_complete_single(client, auth_headers, patient_id, procedure_id)

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    assert list_resp.status_code == 200
    patients = list_resp.json()
    target = next(p for p in patients if p["patient_id"] == patient_id)
    assert target["opportunities"][0]["status"] == "OPEN"
    opportunity_id = target["opportunities"][0]["id"]

    contact_resp = client.patch(
        f"/api/v1/retention/opportunities/{opportunity_id}",
        json={"status": "CONTACTED", "contact_channel": "WHATSAPP"},
        headers=auth_headers,
    )
    assert contact_resp.status_code == 200
    assert contact_resp.json()["status"] == "CONTACTED"

    client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )

    list_resp_after = client.get(
        "/api/v1/retention/opportunities", headers=auth_headers
    )
    remaining_patients = list_resp_after.json()
    assert not any(p["patient_id"] == patient_id for p in remaining_patients)


def test_ciclo_completo_com_booked_fecha_na_nova_venda(
    client, auth_headers, patient_id
):
    """Regressão da revisão final de branch (Finding 1): uma oportunidade
    que avança até BOOKED (paciente concordou em voltar — o caminho de
    sucesso) precisa continuar visível para
    list_open_or_contacted_for_patient_and_procedure() e ser fechada
    quando a venda correspondente de fato acontece. Antes do fix, a
    query de fechamento só considerava OPEN/CONTACTED/NO_RESPONSE, então
    uma oportunidade BOOKED ficava presa para sempre (sem
    resolved_by_sale_id), bloqueando o índice parcial único de permitir
    nova oportunidade para o mesmo item de venda. Este teste falha antes
    do fix (a oportunidade continua BOOKED, resolved_by_sale_id None) e
    passa depois (CLOSED, resolved_by_sale_id == id da nova venda)."""
    procedure_id = _create_procedure(client, auth_headers, interval_days=1)
    _sell_and_complete_single(client, auth_headers, patient_id, procedure_id)

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    target = next(
        p for p in list_resp.json() if p["patient_id"] == patient_id
    )
    opportunity_id = target["opportunities"][0]["id"]
    assert target["opportunities"][0]["status"] == "OPEN"

    contact_resp = client.patch(
        f"/api/v1/retention/opportunities/{opportunity_id}",
        json={"status": "CONTACTED", "contact_channel": "WHATSAPP"},
        headers=auth_headers,
    )
    assert contact_resp.status_code == 200
    assert contact_resp.json()["status"] == "CONTACTED"

    booked_resp = client.patch(
        f"/api/v1/retention/opportunities/{opportunity_id}",
        json={"status": "BOOKED"},
        headers=auth_headers,
    )
    assert booked_resp.status_code == 200
    assert booked_resp.json()["status"] == "BOOKED"

    # BOOKED não aparece mais na tela de reativação (já tem resposta da
    # paciente) — isso é esperado e distinto do fechamento pela venda.
    list_resp_booked = client.get(
        "/api/v1/retention/opportunities", headers=auth_headers
    )
    assert not any(
        p["patient_id"] == patient_id for p in list_resp_booked.json()
    )

    new_sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    assert new_sale_resp.status_code == 201
    new_sale_id = uuid.UUID(new_sale_resp.json()["id"])

    # Não há GET /retention/opportunities/{id}; a tela de reativação só
    # lista status não-terminais e BOOKED/DECLINED já não aparecem nela
    # (ver list_non_terminal_with_details), então a única forma de
    # confirmar o fechamento é consultar a linha diretamente no banco.
    gen = get_tenant_session(_DEV_PROFESSIONAL_ID)
    session = next(gen)
    try:
        opportunity = session.get(ReturnOpportunity, uuid.UUID(opportunity_id))
        assert opportunity is not None
        assert opportunity.status.value == "CLOSED"
        assert opportunity.resolved_by_sale_id == new_sale_id
    finally:
        gen.close()


def test_pacote_com_sessao_pending_nao_aparece_na_lista(
    client, auth_headers, patient_id
):
    procedure_id = _create_procedure(client, auth_headers, interval_days=30)
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "PACKAGE",
            "items": [{"procedure_id": procedure_id, "quantity": 2}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    sessions = sale_resp.json()["sessions"]
    client.patch(
        f"/api/v1/sessions/{sessions[0]['id']}",
        json={"status": "SCHEDULED"},
        headers=auth_headers,
    )
    client.patch(
        f"/api/v1/sessions/{sessions[0]['id']}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    # sessions[1] continua PENDING — item não esgotou.

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    patients = list_resp.json()
    assert not any(p["patient_id"] == patient_id for p in patients)


def test_pacote_de_dez_sessoes_gera_uma_unica_oportunidade(
    client, auth_headers, patient_id
):
    procedure_id = _create_procedure(client, auth_headers, interval_days=30)
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "PACKAGE",
            "items": [{"procedure_id": procedure_id, "quantity": 10}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    sessions = sale_resp.json()["sessions"]
    for s in sessions:
        client.patch(
            f"/api/v1/sessions/{s['id']}",
            json={"status": "SCHEDULED"},
            headers=auth_headers,
        )
        client.patch(
            f"/api/v1/sessions/{s['id']}",
            json={"status": "COMPLETED"},
            headers=auth_headers,
        )

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    target = next(p for p in list_resp.json() if p["patient_id"] == patient_id)
    assert len(target["opportunities"]) == 1
    assert target["opportunities"][0]["potential_value"] == "10000.00"
