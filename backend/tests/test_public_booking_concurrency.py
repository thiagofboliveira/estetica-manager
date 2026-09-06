"""A-04: proteção contra duplo agendamento no link público.

Dois pacientes tentando o mesmo horário recebem 201 no primeiro e 409 Conflict no segundo.
O índice único condicional no banco (uq_bookings_active_slot) e o SELECT ... FOR UPDATE
no caminho de criação garantem serialização e impedem overbooking concorrente.
"""

import random
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.db.session import tenant_session
from app.domain.bookings.enums import BookingStatus
from app.main import app
from app.models.booking import Booking


def _setup_public_agenda(client: TestClient, slug: str) -> tuple[dict, str, UUID]:
    login_resp = client.post("/dev/login")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    me_resp = client.get("/api/v1/users/me", headers=auth_headers)
    assert me_resp.status_code == 200
    prof_id = UUID(me_resp.json()["id"])

    profile_update = client.patch(
        "/api/v1/users/me/public-profile",
        json={"slug": slug, "bio": "Teste de concorrencia"},
        headers=auth_headers,
    )
    assert profile_update.status_code == 200, profile_update.text

    proc_resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Procedimento Teste Concorrencia",
            "type": "SERVICE",
            "price": "250.00",
            "estimated_cost": "50.00",
            "session_plan": "SINGLE",
        },
        headers=auth_headers,
    )
    assert proc_resp.status_code == 201
    return auth_headers, proc_resp.json()["id"], prof_id



def _next_free_slot(client: TestClient, slug: str) -> tuple[date, str]:
    target_day = date.today() + timedelta(days=500 + random.randint(1, 1000))
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


def test_duplo_agendamento_mesmo_horario_rejeita_com_409():
    client = TestClient(app)
    slug = f"dra-concorrencia-{random.randint(10000, 99999)}"
    _, procedure_id, _ = _setup_public_agenda(client, slug)
    target_day, slot = _next_free_slot(client, slug)
    sched = _scheduled_at(target_day, slot)

    # 1º agendamento tem sucesso
    resp1 = client.post(
        f"/api/v1/public/agenda/{slug}/bookings",
        json={
            "procedure_id": procedure_id,
            "scheduled_at": sched,
            "patient_name": "Paciente Um",
            "patient_phone": f"1198{random.randint(1000000, 9999999)}",
        },
    )
    assert resp1.status_code == 201, resp1.text

    # 2º agendamento para o mesmo horário exato deve falhar com 409 Conflict
    resp2 = client.post(
        f"/api/v1/public/agenda/{slug}/bookings",
        json={
            "procedure_id": procedure_id,
            "scheduled_at": sched,
            "patient_name": "Paciente Dois",
            "patient_phone": f"1198{random.randint(1000000, 9999999)}",
        },
    )
    assert resp2.status_code == 409
    assert "este horário acabou de ser ocupado" in resp2.json()["detail"].lower()


def test_constraint_banco_impede_duplicacao_direta():
    # Testa a constraint de banco uq_bookings_active_slot diretamente
    client = TestClient(app)
    slug = f"dra-db-constraint-{random.randint(10000, 99999)}"
    _, procedure_id, prof_id = _setup_public_agenda(client, slug)
    target_day, slot = _next_free_slot(client, slug)
    sched_dt = datetime.strptime(slot, "%H:%M").time()
    sp_tz = ZoneInfo("America/Sao_Paulo")
    sched_utc = datetime.combine(target_day, sched_dt).replace(tzinfo=sp_tz).astimezone(UTC)

    with tenant_session(prof_id) as session1:
        b1 = Booking(
            professional_id=prof_id,
            scheduled_at=sched_utc,
            patient_name_hint="Teste DB 1",
            procedure_id=procedure_id,
            status=BookingStatus.SCHEDULED,
            management_token=f"token-1-{random.randint(1000, 9999)}",
        )
        session1.add(b1)

    with pytest.raises(IntegrityError), tenant_session(prof_id) as session2:
        b2 = Booking(
            professional_id=prof_id,
            scheduled_at=sched_utc,
            patient_name_hint="Teste DB 2",
            procedure_id=procedure_id,
            status=BookingStatus.SCHEDULED,
            management_token=f"token-2-{random.randint(1000, 9999)}",
        )
        session2.add(b2)

