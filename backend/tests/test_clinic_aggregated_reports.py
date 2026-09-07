import time
from datetime import date
from decimal import Decimal
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import tenant_session, unsafe_session_without_tenant
from app.main import app
from app.models.clinic import Clinic
from app.models.financial_settings import FeePayer, SplitBase
from app.models.fixed_expense import ExpensePeriodicity, FixedExpense
from app.models.patient import Patient
from app.models.procedure import Modality, Procedure
from app.models.professional import Professional
from app.models.sale import PaymentMethod, Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.user import User

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


def _make_auth_header(user_id: str) -> dict[str, str]:
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": user_id,
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "role": settings.SUPABASE_JWT_AUDIENCE,
            "iat": now,
            "exp": now + 3600,
        },
        settings.DEV_AUTH_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_clinic_aggregated_reports_and_security(client: TestClient):
    clinic_a_id = uuid4()
    clinic_b_id = uuid4()
    admin_id = uuid4()
    staff_id = uuid4()
    other_clinic_prof_id = uuid4()

    # 1. Provisiona clínicas e profissionais
    with unsafe_session_without_tenant("setup clinic test") as session:
        clinic_a = Clinic(id=clinic_a_id, name=f"Clínica A {clinic_a_id.hex[:4]}")
        clinic_b = Clinic(id=clinic_b_id, name=f"Clínica B {clinic_b_id.hex[:4]}")

        admin_user = User(
            id=admin_id,
            clinic_id=clinic_a_id,
            name="Dona da Clínica",
            email=f"dona_{admin_id.hex[:6]}@example.com",
            role="admin",
            is_active=True,
        )
        staff_user = User(
            id=staff_id,
            clinic_id=clinic_a_id,
            name="Profissional da Equipe",
            email=f"staff_{staff_id.hex[:6]}@example.com",
            role="user",
            is_active=True,
        )
        other_user = User(
            id=other_clinic_prof_id,
            clinic_id=clinic_b_id,
            name="Profissional Outra Clínica",
            email=f"other_{other_clinic_prof_id.hex[:6]}@example.com",
            role="user",
            is_active=True,
        )

        admin_prof = Professional(
            id=admin_id,
            user_id=admin_id,
            clinic_id=clinic_a_id,
            name="Dona da Clínica",
            timezone="America/Sao_Paulo",
            is_active=True,
        )
        staff_prof = Professional(
            id=staff_id,
            user_id=staff_id,
            clinic_id=clinic_a_id,
            name="Profissional da Equipe",
            timezone="America/Sao_Paulo",
            is_active=True,
        )
        other_prof = Professional(
            id=other_clinic_prof_id,
            user_id=other_clinic_prof_id,
            clinic_id=clinic_b_id,
            name="Profissional Outra Clínica",
            timezone="America/Sao_Paulo",
            is_active=True,
        )

        session.add_all([clinic_a, clinic_b])
        session.flush()
        session.add_all([admin_user, staff_user, other_user])
        session.flush()
        session.add_all([admin_prof, staff_prof, other_prof])
        session.flush()

    # 2. Insere dados sob tenant isolado para Admin (Venda R$ 100, Despesa Fixa R$ 50)
    with tenant_session(admin_id) as sess:
        p1 = Patient(professional_id=admin_id, name="Paciente Admin", phone="11911111111", is_active=True)
        sess.add(p1)
        sess.flush()

        proc1 = Procedure(
            professional_id=admin_id,
            name="Procedimento Geral",
            price="100.00",
            estimated_cost="20.00",
            default_modality=Modality.IN_PERSON,
            is_active=True,
        )
        sess.add(proc1)
        sess.flush()

        sale1 = Sale(
            professional_id=admin_id,
            patient_id=p1.id,
            type=SaleType.SINGLE,
            sold_at=date.today(),
            items_total=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            gross_amount=Decimal("100.00"),
            split_applied=Decimal("0.00"),
            split_amount_applied=Decimal("0.00"),
            split_base_applied=SplitBase.GROSS,
            fee_payer_applied=FeePayer.PROFESSIONAL,
            fee_applied=Decimal("0.00"),
            fee_amount_applied=Decimal("0.00"),
            cost_provisioned=Decimal("20.00"),
            cost_realized=Decimal("20.00"),
            net_profit=Decimal("80.00"),
            payment_method=PaymentMethod.PIX,
            installments=1,
            status=SaleStatus.ACTIVE,
        )
        sess.add(sale1)
        sess.flush()

        item1 = SaleItem(
            professional_id=admin_id,
            sale_id=sale1.id,
            procedure_id=proc1.id,
            quantity=1,
            unit_price=Decimal("100.00"),
            unit_cost_estimated=Decimal("20.00"),
            discount_allocated=Decimal("0.00"),
        )
        sess.add(item1)

        exp1 = FixedExpense(
            professional_id=admin_id,
            label="Aluguel Admin",
            amount=Decimal("50.00"),
            periodicity=ExpensePeriodicity.MONTHLY,
            category="INFRAESTRUTURA",
            active_from=date(2020, 1, 1),
            active_to=None,
        )
        sess.add(exp1)

    # 3. Insere dados sob tenant isolado para Staff (Venda R$ 200, Despesa Fixa R$ 150)
    with tenant_session(staff_id) as sess:
        p2 = Patient(professional_id=staff_id, name="Paciente Staff", phone="11922222222", is_active=True)
        sess.add(p2)
        sess.flush()

        proc2 = Procedure(
            professional_id=staff_id,
            name="Procedimento Especializado",
            price=Decimal("200.00"),
            estimated_cost=Decimal("40.00"),
            default_modality=Modality.IN_PERSON,
            is_active=True,
        )
        sess.add(proc2)
        sess.flush()

        sale2 = Sale(
            professional_id=staff_id,
            patient_id=p2.id,
            type=SaleType.SINGLE,
            sold_at=date.today(),
            items_total=Decimal("200.00"),
            discount_amount=Decimal("0.00"),
            gross_amount=Decimal("200.00"),
            split_applied=Decimal("0.00"),
            split_amount_applied=Decimal("0.00"),
            split_base_applied=SplitBase.GROSS,
            fee_payer_applied=FeePayer.PROFESSIONAL,
            fee_applied=Decimal("0.00"),
            fee_amount_applied=Decimal("0.00"),
            cost_provisioned=Decimal("40.00"),
            cost_realized=Decimal("40.00"),
            net_profit=Decimal("160.00"),
            payment_method=PaymentMethod.PIX,
            installments=1,
            status=SaleStatus.ACTIVE,
        )
        sess.add(sale2)
        sess.flush()

        item2 = SaleItem(
            professional_id=staff_id,
            sale_id=sale2.id,
            procedure_id=proc2.id,
            quantity=1,
            unit_price=Decimal("200.00"),
            unit_cost_estimated=Decimal("40.00"),
            discount_allocated=Decimal("0.00"),
        )
        sess.add(item2)

        exp2 = FixedExpense(
            professional_id=staff_id,
            label="Software Staff",
            amount=Decimal("150.00"),
            periodicity=ExpensePeriodicity.MONTHLY,
            category="SISTEMAS",
            active_from=date(2020, 1, 1),
            active_to=None,
        )
        sess.add(exp2)

    admin_headers = _make_auth_header(str(admin_id))
    staff_headers = _make_auth_header(str(staff_id))

    # --- TESTE A: Admin com escopo de clínica consolidado ---
    resp_clinic = client.get("/api/v1/dashboard?scope=clinic", headers=admin_headers)
    assert resp_clinic.status_code == 200, resp_clinic.text
    data_clinic = resp_clinic.json()
    assert data_clinic["scope"] == "clinic"
    assert data_clinic["professionals_count"] == 2
    assert float(data_clinic["gross_revenue"]) == 300.00
    assert data_clinic["sale_count"] == 2
    assert float(data_clinic["fixed_expenses_total"]) == 200.00

    # --- TESTE B: Admin filtrando profissional específico da sua equipe ---
    resp_staff_filter = client.get(
        f"/api/v1/dashboard?professional_id={staff_id}", headers=admin_headers
    )
    assert resp_staff_filter.status_code == 200, resp_staff_filter.text
    data_staff_filter = resp_staff_filter.json()
    assert data_staff_filter["scope"] == "professional"
    assert float(data_staff_filter["gross_revenue"]) == 200.00
    assert data_staff_filter["sale_count"] == 1
    assert float(data_staff_filter["fixed_expenses_total"]) == 150.00

    # --- TESTE C: Admin no escopo padrão ("me") ---
    resp_me = client.get("/api/v1/dashboard?scope=me", headers=admin_headers)
    assert resp_me.status_code == 200
    data_me = resp_me.json()
    assert data_me["scope"] == "me"
    assert float(data_me["gross_revenue"]) == 100.00
    assert data_me["sale_count"] == 1
    assert float(data_me["fixed_expenses_total"]) == 50.00

    # --- TESTE D: Ranking de procedimentos e despesas agregadas ---
    resp_ranking = client.get(
        "/api/v1/reports/procedures?scope=clinic", headers=admin_headers
    )
    assert resp_ranking.status_code == 200
    ranking_data = resp_ranking.json()
    assert ranking_data["scope"] == "clinic"
    assert ranking_data["professionals_count"] == 2
    assert len(ranking_data["rows"]) == 2

    resp_expenses = client.get(
        "/api/v1/reports/expenses-by-category?scope=clinic", headers=admin_headers
    )
    assert resp_expenses.status_code == 200
    expenses_data = resp_expenses.json()
    total_expenses = sum(float(r["monthly_amount"]) for r in expenses_data["rows"])
    assert total_expenses == 200.00

    # --- TESTE E: Segurança - Usuário comum (não admin) não pode ver escopo de clínica ---
    resp_forbidden = client.get("/api/v1/dashboard?scope=clinic", headers=staff_headers)
    assert resp_forbidden.status_code == 403

    resp_forbidden_filter = client.get(
        f"/api/v1/dashboard?professional_id={admin_id}", headers=staff_headers
    )
    assert resp_forbidden_filter.status_code == 403

    # Usuário comum vê perfeitamente seus próprios dados no padrão
    resp_staff_me = client.get("/api/v1/dashboard", headers=staff_headers)
    assert resp_staff_me.status_code == 200
    assert float(resp_staff_me.json()["gross_revenue"]) == 200.00
    assert resp_staff_me.json()["sale_count"] == 1

    # --- TESTE F: Segurança - Admin não pode passar professional_id de outra clínica ---
    resp_cross_clinic = client.get(
        f"/api/v1/dashboard?professional_id={other_clinic_prof_id}",
        headers=admin_headers,
    )
    assert resp_cross_clinic.status_code == 404
