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

    def test_login_emite_first_login(
        self, client: TestClient, auth_headers: dict[str, str], professional_id: str
    ) -> None:
        before = _event_count("first_login", professional_id)
        resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        after = _event_count("first_login", professional_id)
        assert after >= 1
        assert after in (before, before + 1)

    def test_dashboard_emite_first_profit_viewed_quando_ha_dados(
        self, client: TestClient, auth_headers: dict[str, str], professional_id: str
    ) -> None:
        before = _event_count("first_profit_viewed", professional_id)
        # Cria paciente, procedimento e venda para garantir has_any_data=True
        pat_resp = client.post("/api/v1/patients", json={"name": f"Pat Profit {uuid.uuid4()}"}, headers=auth_headers)
        proc_resp = client.post("/api/v1/procedures", json={"name": f"Proc Profit {uuid.uuid4()}", "price": "150.00", "estimated_cost": "50.00"}, headers=auth_headers)
        client.post("/api/v1/sales", json={
            "patient_id": pat_resp.json()["id"],
            "type": "SINGLE",
            "items": [{"procedure_id": proc_resp.json()["id"], "quantity": 1}],
            "payment_method": "PIX",
            "installments": 1,
        }, headers=auth_headers)

        dash_resp = client.get("/api/v1/dashboard", headers=auth_headers)
        assert dash_resp.status_code == 200
        assert dash_resp.json()["has_any_data"] is True
        after = _event_count("first_profit_viewed", professional_id)
        assert after >= max(before, 1)

    def test_retencao_contato_emite_first_reactivation_sent_e_converted(
        self, client: TestClient, auth_headers: dict[str, str], professional_id: str
    ) -> None:
        from datetime import date, timedelta

        from sqlalchemy import text

        from app.db.session import unsafe_session_without_tenant
        from app.domain.retention.enums import ReturnOpportunityStatus
        from app.models.return_opportunity import ReturnOpportunity

        pat_resp = client.post("/api/v1/patients", json={"name": f"Pat Ret {uuid.uuid4()}"}, headers=auth_headers)
        proc_resp = client.post("/api/v1/procedures", json={"name": f"Proc Ret {uuid.uuid4()}", "price": "200.00", "estimated_cost": "40.00"}, headers=auth_headers)
        patient_id = uuid.UUID(pat_resp.json()["id"])
        procedure_id = uuid.UUID(proc_resp.json()["id"])

        # Cria oportunidade de retorno diretamente no banco
        opp_id = uuid.uuid4()
        with unsafe_session_without_tenant("test: criar oportunidade") as session:
            session.execute(text("SELECT set_config('app.professional_id', :pid, true)"), {"pid": professional_id})
            opp = ReturnOpportunity(
                id=opp_id,
                professional_id=uuid.UUID(professional_id),
                patient_id=patient_id,
                procedure_id=procedure_id,
                due_date=date.today() - timedelta(days=10),
                status=ReturnOpportunityStatus.OPEN,
            )
            session.add(opp)
            session.flush()

        sent_before = _event_count("first_reactivation_sent", professional_id)
        # Registra contato
        patch_resp = client.patch(
            f"/api/v1/retention/opportunities/{opp_id}",
            json={"status": "CONTACTED", "contact_channel": "WHATSAPP"},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200, patch_resp.text
        sent_after = _event_count("first_reactivation_sent", professional_id)
        assert sent_after >= max(sent_before, 1)

        conv_before = _event_count("first_reactivation_converted", professional_id)
        # Nova venda para o mesmo paciente e procedimento deve fechar a oportunidade e emitir first_reactivation_converted
        sale_resp = client.post("/api/v1/sales", json={
            "patient_id": str(patient_id),
            "type": "SINGLE",
            "items": [{"procedure_id": str(procedure_id), "quantity": 1}],
            "payment_method": "PIX",
            "installments": 1,
        }, headers=auth_headers)
        assert sale_resp.status_code == 201, sale_resp.text
        conv_after = _event_count("first_reactivation_converted", professional_id)
        assert conv_after >= max(conv_before, 1)

    def test_booking_publico_emite_eventos_e_incrementa_contador_dashboard(
        self, client: TestClient, auth_headers: dict[str, str], professional_id: str
    ) -> None:
        slug = f"prof-event-test-{uuid.uuid4().hex[:6]}"
        client.patch(
            "/api/v1/users/me/public-profile",
            json={"slug": slug, "bio": "Bio evento"},
            headers=auth_headers,
        )
        proc_resp = client.post(
            "/api/v1/procedures",
            json={"name": f"Proc Event {uuid.uuid4()}", "price": "180.00", "estimated_cost": "30.00"},
            headers=auth_headers,
        )
        proc_id = proc_resp.json()["id"]

        from datetime import UTC, datetime, timedelta
        sched_time = (datetime.now(UTC) + timedelta(days=200, hours=uuid.uuid4().int % 20 + 1)).replace(microsecond=0)

        # Booking público (anônimo, sem auth)
        book_resp = client.post(
            f"/api/v1/public/agenda/{slug}/bookings",
            json={
                "procedure_id": proc_id,
                "scheduled_at": sched_time.isoformat(),
                "patient_name": "Paciente Link Publico",
                "patient_phone": "11999998888",
                "patient_consent_whatsapp": True,
            },
        )
        assert book_resp.status_code == 201, book_resp.text

        # Verifica eventos emitidos
        assert _event_count("first_public_booking_received", professional_id) >= 1
        assert _event_count("public_booking_created", professional_id) >= 1

        # Verifica contador no dashboard da profissional
        dash = client.get("/api/v1/dashboard", headers=auth_headers)
        assert dash.status_code == 200
        assert dash.json()["public_booking_count"] >= 1

