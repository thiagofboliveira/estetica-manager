"""Testes de integração para a funcionalidade de link público de agendamento e auto-gestão de horários."""

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app


def test_public_agenda_and_booking_flow():
    client = TestClient(app)

    # 1. Login profissional para configurar o perfil público e cadastrar um procedimento
    login_resp = client.post("/dev/login")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Configura slug e bio da profissional
    test_slug = "dra-test-public-agenda"
    profile_update = client.patch(
        "/api/v1/users/me/public-profile",
        json={"slug": test_slug, "bio": "Especialista em estética facial e corporal."},
        headers=auth_headers,
    )
    assert profile_update.status_code == 200, profile_update.text
    assert profile_update.json()["slug"] == test_slug
    assert profile_update.json()["bio"] == "Especialista em estética facial e corporal."

    # Cadastra um procedimento de teste (tipo SERVICE)
    proc_resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Limpeza de Pele Profunda",
            "type": "SERVICE",
            "price": "250.00",
            "estimated_cost": "50.00",
            "return_interval_days": 30,
            "session_plan": "SINGLE",
        },
        headers=auth_headers,
    )
    assert proc_resp.status_code == 201
    procedure_id = proc_resp.json()["id"]

    # 2. Acesso PÚBLICO desautenticado à agenda (ex: visitante vindo da bio do Instagram)
    agenda_resp = client.get(f"/api/v1/public/agenda/{test_slug}")
    assert agenda_resp.status_code == 200, agenda_resp.text
    agenda_data = agenda_resp.json()
    assert agenda_data["slug"] == test_slug
    assert agenda_data["bio"] == "Especialista em estética facial e corporal."
    assert any(p["id"] == procedure_id for p in agenda_data["procedures"])

    # 3. Consulta de slots livres para uma data futura aleatória para garantir isolamento
    import random

    target_day = date.today() + timedelta(days=50 + random.randint(1, 500))
    slots_resp = client.get(
        f"/api/v1/public/agenda/{test_slug}/slots",
        params={"date": target_day.isoformat()},
    )
    assert slots_resp.status_code == 200
    available_slots = slots_resp.json()
    assert isinstance(available_slots, list)
    assert len(available_slots) >= 2, "A agenda deve retornar slots livres configurados"

    # 4. Cria agendamento público no primeiro slot disponível
    # Os slots retornados por get_public_slots são horários locais da profissional (America/Sao_Paulo)
    from zoneinfo import ZoneInfo
    sp_tz = ZoneInfo("America/Sao_Paulo")

    first_slot_time = datetime.strptime(available_slots[0], "%H:%M").time()
    scheduled_time = datetime.combine(target_day, first_slot_time).replace(tzinfo=sp_tz).astimezone(UTC)

    booking_payload = {
        "procedure_id": procedure_id,
        "scheduled_at": scheduled_time.isoformat(),
        "patient_name": "Juliana Silveira",
        "patient_phone": "11988887777",
        "note": "Primeira vez na clínica",
    }

    create_booking_resp = client.post(
        f"/api/v1/public/agenda/{test_slug}/bookings",
        json=booking_payload,
    )
    assert create_booking_resp.status_code == 201, create_booking_resp.text
    booking = create_booking_resp.json()
    booking_id = booking["id"]
    management_token = booking["management_token"]
    assert booking["patient_name"] == "Juliana Silveira"
    assert booking["patient_phone"] == "11988887777"
    assert booking["status"] == "SCHEDULED"
    assert len(management_token) >= 20

    # 4.1. O horário agendado DEVE SUMIR dos slots livres públicos daquele dia
    updated_slots_resp = client.get(
        f"/api/v1/public/agenda/{test_slug}/slots",
        params={"date": target_day.isoformat()},
    )
    assert updated_slots_resp.status_code == 200
    updated_slots = updated_slots_resp.json()
    assert available_slots[0] not in updated_slots, (
        f"O horário {available_slots[0]} deve ter sido removido dos slots públicos após ser agendado"
    )

    # 4.2. O agendamento DEVE APARECER na agenda privada da profissional
    agenda_resp = client.get(
        "/api/v1/sessions",
        params={"from": target_day.isoformat(), "to": target_day.isoformat()},
        headers=auth_headers,
    )
    assert agenda_resp.status_code == 200
    private_agenda_items = agenda_resp.json()
    matched_booking = next((item for item in private_agenda_items if item["id"] == str(booking_id)), None)
    assert matched_booking is not None, "O booking público deve constar na agenda da profissional"
    assert matched_booking["type"] == "BOOKING"
    assert matched_booking["patient_name"] == "Juliana Silveira"
    assert matched_booking["procedure_name"] == "Limpeza de Pele Profunda"
    assert matched_booking["status"] == "SCHEDULED"
    assert matched_booking["confirmed_at"] is None

    # 4.3. Profissional confirma o agendamento
    confirm_resp = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers,
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirmed_data = confirm_resp.json()
    assert confirmed_data["confirmed_at"] is not None

    # 4.4. A agenda privada agora deve refletir confirmed_at preenchido
    agenda_resp_after_confirm = client.get(
        "/api/v1/sessions",
        params={"from": target_day.isoformat(), "to": target_day.isoformat()},
        headers=auth_headers,
    )
    assert agenda_resp_after_confirm.status_code == 200
    matched_confirmed = next((item for item in agenda_resp_after_confirm.json() if item["id"] == str(booking_id)), None)
    assert matched_confirmed is not None
    assert matched_confirmed["confirmed_at"] is not None

    # 4.5. A agenda pública continua marcando o slot como ocupado
    slots_resp_after_confirm = client.get(
        f"/api/v1/public/agenda/{test_slug}/slots",
        params={"date": target_day.isoformat()},
    )
    assert available_slots[0] not in slots_resp_after_confirm.json()

    # 5. Tentativa de agendamento duplicado no mesmo horário (deve retornar 409 Conflict)
    conflict_resp = client.post(
        f"/api/v1/public/agenda/{test_slug}/bookings",
        json=booking_payload,
    )
    assert conflict_resp.status_code == 409
    assert (
        "conflito" in conflict_resp.json()["detail"].lower()
        or "ocupado" in conflict_resp.json()["detail"].lower()
    )

    # 6. Paciente visualiza seu agendamento através do token seguro
    view_resp = client.get(
        f"/api/v1/public/bookings/{booking_id}",
        params={"token": management_token},
    )
    assert view_resp.status_code == 200
    assert view_resp.json()["id"] == booking_id
    assert view_resp.json()["procedure_name"] == "Limpeza de Pele Profunda"

    # Tentativa de acesso com token inválido deve dar 404
    invalid_token_resp = client.get(
        f"/api/v1/public/bookings/{booking_id}",
        params={"token": "invalid_fake_token_12345"},
    )
    assert invalid_token_resp.status_code == 404

    try:
        # 7. Paciente remarca para outro slot disponível
        second_slot_time = datetime.strptime(available_slots[1], "%H:%M").time()
        new_scheduled_time = datetime.combine(target_day, second_slot_time).replace(
            tzinfo=sp_tz
        ).astimezone(UTC)

        reschedule_resp = client.patch(
            f"/api/v1/public/bookings/{booking_id}/reschedule",
            params={"token": management_token},
            json={"scheduled_at": new_scheduled_time.isoformat()},
        )
        assert reschedule_resp.status_code == 200, reschedule_resp.text
        assert (
            datetime.fromisoformat(reschedule_resp.json()["scheduled_at"])
            == new_scheduled_time
        )

        # 8. Paciente cancela o agendamento através do token seguro
        cancel_resp = client.post(
            f"/api/v1/public/bookings/{booking_id}/cancel",
            params={"token": management_token},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "CANCELLED"
    finally:
        # Restaura perfil original para testes manuais e navegação
        client.patch(
            "/api/v1/users/me/public-profile",
            json={
                "slug": "dra-camila",
                "bio": "Especialista em Harmonização Facial, Bioestimuladores de Colágeno e Rejuvenescimento Natural.",
                "specialty": "Biomédica Esteta • CRM/CRBM 12345",
                "avatar_url": "https://images.unsplash.com/photo-1594824813585-6188e7a0305f?auto=format&fit=crop&w=400&q=80",
            },
            headers=auth_headers,
        )
