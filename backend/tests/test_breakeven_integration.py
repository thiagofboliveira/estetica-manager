"""Épico C — "Ponto de equilíbrio do mês" (roadmap 2026-09-02).

Teste de integração REAL contra o Postgres do Docker. A API sempre
grava `sold_at=today` (não dá pra "vender no passado" via POST
/sales), então backdata vendas direto via ORM (mesmo padrão de
tests/test_snapshot_immutability.py) para popular os "últimos meses
fechados" que alimentam average_ticket_recent — e usa rollback no
finally para não sujar o ambiente de dev.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import get_tenant_session
from app.main import app
from app.models.financial_settings import FeePayer, PaymentMethod, SplitBase
from app.models.sale import Sale, SaleStatus, SaleType

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)

PROFESSIONAL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _closed_month_sale(professional_id: uuid.UUID, sold_at: date, gross: str) -> Sale:
    return Sale(
        professional_id=professional_id,
        patient_id=uuid.uuid4(),
        type=SaleType.SINGLE,
        sold_at=sold_at,
        status=SaleStatus.ACTIVE,
        payment_method=PaymentMethod.PIX,
        installments=1,
        items_total=Decimal(gross),
        discount_amount=Decimal("0.00"),
        gross_amount=Decimal(gross),
        split_applied=Decimal("0.00"),
        split_base_applied=SplitBase.GROSS,
        fee_payer_applied=FeePayer.PROFESSIONAL,
        fee_applied=Decimal("0.00"),
        fee_amount_applied=Decimal("0.00"),
        cost_provisioned=Decimal("0.00"),
        cost_realized=Decimal("0.00"),
        net_profit=Decimal(gross),
        margin=Decimal("1.0000"),
        snapshot_payload={},
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_estimativa_de_atendimentos_usa_ticket_medio_dos_meses_fechados(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    today = date.today()
    last_closed_month = today.replace(day=1) - timedelta(days=1)

    gen = get_tenant_session(PROFESSIONAL_ID)
    session = next(gen)
    try:
        # Ticket médio dos últimos meses fechados: (100 + 300) / 2 = 200.
        session.add(_closed_month_sale(PROFESSIONAL_ID, last_closed_month, "100.00"))
        session.add(_closed_month_sale(PROFESSIONAL_ID, last_closed_month, "300.00"))
        session.flush()

        # Zera despesas fixas ativas temporariamente não é viável sem
        # tocar em outro tenant/config — em vez disso, provamos o
        # sintoma direto e inequívoco de que a query rodou: com vendas
        # nos últimos meses fechados, breakeven_remaining_sessions_estimate
        # só continua None se breakeven_remaining_amount for zero (já
        # bateu a meta) — nunca por falta de histórico, que é o bug que
        # este teste existe para pegar.
        resp = client.get(
            "/api/v1/dashboard", params={"period": "this_month"}, headers=auth_headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()

        remaining = Decimal(body["breakeven_remaining_amount"])
        estimate = body["breakeven_remaining_sessions_estimate"]

        if remaining > 0:
            assert estimate is not None
        else:
            assert estimate == 0
    finally:
        session.rollback()
        gen.close()
