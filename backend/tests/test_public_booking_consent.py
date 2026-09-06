"""A-02/A-02a: consentimento de WhatsApp capturado no agendamento público.

A paciente que agenda pelo link público informa nome e telefone sem estar
autenticada. O produto proíbe contato por WhatsApp sem `consent_whatsapp`
(opportunity_rules.py) — sem este teste, o formulário público criava
pacientes sempre com consentimento ausente (default do model), tornando
todo lead do link público um lead que o próprio produto se recusa a
contatar.
"""

import random
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import app


def _setup_public_agenda(client: TestClient, slug: str) -> tuple[dict, str]:
    login_resp = client.post("/dev/login")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    profile_update = client.patch(
        "/api/v1/users/me/public-profile",
        json={"slug": slug, "bio": "Teste de consentimento"},
        headers=auth_headers,
    )
    assert profile_update.status_code == 200, profile_update.text

    proc_resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Procedimento Teste Consentimento",
            "type": "SERVICE",
            "price": "200.00",
            "estimated_cost": "40.00",
            "session_plan": "SINGLE",
        },
        headers=auth_headers,
    )
    assert proc_resp.status_code == 201
    return auth_headers, proc_resp.json()["id"]


def _next_free_slot(client: TestClient, slug: str) -> tuple[date, str]:
    target_day = date.today() + timedelta(days=60 + random.randint(1, 500))
    slots_resp = client.get(
        f"/api/v1/public/agenda/{slug}/slots",
        params={"date": target_day.isoformat()},
    )
    assert slots_resp.status_code == 200
    slots = slots_resp.json()
    assert len(slots) >= 1
    return target_day, slots[0]


def _scheduled_at(target_day: date, slot: str) -> str:
    sp_tz = ZoneInfo("America/Sao_Paulo")
    t = datetime.strptime(slot, "%H:%M").time()
    return (
        datetime.combine(target_day, t).replace(tzinfo=sp_tz).astimezone(UTC).isoformat()
    )


def _random_phone() -> str:
    """Telefone único por execução: os testes rodam contra o Postgres de
    dev real, sem isolamento transacional entre execuções (não há
    conftest de rollback), então um número fixo colide com lixo de uma
    rodada anterior e o teste vira flaky."""
    return f"1199{random.randint(1000000, 9999999)}"


def _patient_by_phone(client: TestClient, headers: dict, phone: str) -> dict:
    resp = client.get("/api/v1/patients", params={"search": phone}, headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"] if "items" in resp.json() else resp.json()
    matches = [p for p in items if p["phone"] == phone]
    assert len(matches) == 1, f"esperado 1 paciente com {phone}, achou {len(matches)}"
    return matches[0]


def test_booking_publico_sem_consentimento_nao_habilita_whatsapp():
    client = TestClient(app)
    slug = "dra-test-sem-consentimento"
    auth_headers, procedure_id = _setup_public_agenda(client, slug)
    target_day, slot = _next_free_slot(client, slug)
    phone = _random_phone()

    resp = client.post(
        f"/api/v1/public/agenda/{slug}/bookings",
        json={
            "procedure_id": procedure_id,
            "scheduled_at": _scheduled_at(target_day, slot),
            "patient_name": "Beatriz Sem Consentimento",
            "patient_phone": phone,
            # patient_consent_whatsapp omitido -> default False
        },
    )
    assert resp.status_code == 201, resp.text

    normalized = f"+55{phone}"
    patient = _patient_by_phone(client, auth_headers, normalized)
    assert patient["consent_whatsapp"] is False


def test_booking_publico_com_consentimento_habilita_whatsapp():
    client = TestClient(app)
    slug = "dra-test-com-consentimento"
    auth_headers, procedure_id = _setup_public_agenda(client, slug)
    target_day, slot = _next_free_slot(client, slug)
    phone = _random_phone()

    resp = client.post(
        f"/api/v1/public/agenda/{slug}/bookings",
        json={
            "procedure_id": procedure_id,
            "scheduled_at": _scheduled_at(target_day, slot),
            "patient_name": "Carla Com Consentimento",
            "patient_phone": phone,
            "patient_consent_whatsapp": True,
        },
    )
    assert resp.status_code == 201, resp.text

    normalized = f"+55{phone}"
    patient = _patient_by_phone(client, auth_headers, normalized)
    assert patient["consent_whatsapp"] is True
    assert patient["consent_at"] is not None


def test_booking_publico_com_consentimento_nao_rebaixa_consentimento_existente():
    """Paciente que já tinha consent_whatsapp=True e agenda de novo sem
    marcar o checkbox não perde o consentimento — retirar é ato explícito
    em PatientService.update, não efeito colateral de um novo agendamento."""
    client = TestClient(app)
    slug = "dra-test-preserva-consentimento"
    auth_headers, procedure_id = _setup_public_agenda(client, slug)
    phone = _random_phone()

    create_patient_resp = client.post(
        "/api/v1/patients",
        json={
            "name": "Denise Já Consentiu",
            "phone": phone,
            "consent_whatsapp": True,
        },
        headers=auth_headers,
    )
    assert create_patient_resp.status_code == 201, create_patient_resp.text

    target_day, slot = _next_free_slot(client, slug)
    resp = client.post(
        f"/api/v1/public/agenda/{slug}/bookings",
        json={
            "procedure_id": procedure_id,
            "scheduled_at": _scheduled_at(target_day, slot),
            "patient_name": "Denise Já Consentiu",
            "patient_phone": phone,
            "patient_consent_whatsapp": False,
        },
    )
    assert resp.status_code == 201, resp.text

    normalized = f"+55{phone}"
    patient = _patient_by_phone(client, auth_headers, normalized)
    assert patient["consent_whatsapp"] is True
