"""T-020b — listener before_flush bloqueia UPDATE em campos congelados
de Sale (invariante I3). Integração real: precisa de sessão de banco de
verdade (o listener é registrado em Session, e o flush real dispara a
checagem de histórico de atributos)."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import settings
from app.db.session import get_tenant_session
from app.models.financial_settings import FeePayer, PaymentMethod, SplitBase
from app.models.listeners import ImmutableFieldError
from app.models.sale import Sale, SaleStatus, SaleType

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer Postgres real"
)

PROFESSIONAL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_sale(professional_id: uuid.UUID) -> Sale:
    return Sale(
        professional_id=professional_id,
        patient_id=uuid.uuid4(),
        type=SaleType.SINGLE,
        sold_at=datetime.now(UTC).date(),
        status=SaleStatus.ACTIVE,
        payment_method=PaymentMethod.PIX,
        installments=1,
        items_total=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        gross_amount=Decimal("100.00"),
        split_applied=Decimal("0.00"),
        split_base_applied=SplitBase.GROSS,
        fee_payer_applied=FeePayer.PROFESSIONAL,
        fee_applied=Decimal("0.00"),
        fee_amount_applied=Decimal("0.00"),
        cost_provisioned=Decimal("10.00"),
        cost_realized=Decimal("10.00"),
        net_profit=Decimal("90.00"),
        margin=Decimal("0.9000"),
        snapshot_payload={},
    )


def test_update_em_campo_congelado_levanta_erro() -> None:
    gen = get_tenant_session(PROFESSIONAL_ID)
    session = next(gen)
    try:
        sale = _make_sale(PROFESSIONAL_ID)
        session.add(sale)
        session.flush()

        sale.net_profit = Decimal("999.00")  # tentativa de alterar congelado
        with pytest.raises(ImmutableFieldError):
            session.flush()
    finally:
        session.rollback()
        gen.close()


def test_atualizar_cost_realized_e_permitido() -> None:
    """Única exceção intencional (§12.1) — cost_realized muda quando
    sessões completam/expiram."""
    gen = get_tenant_session(PROFESSIONAL_ID)
    session = next(gen)
    try:
        sale = _make_sale(PROFESSIONAL_ID)
        session.add(sale)
        session.flush()

        sale.cost_realized = Decimal("5.00")
        session.flush()  # não deve levantar
    finally:
        session.rollback()
        gen.close()
