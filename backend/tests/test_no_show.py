from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.financial.dashboard import (
    FixedExpenseForDashboard,
    PeriodKind,
    SaleForDashboard,
    build_dashboard,
)
from app.domain.messaging.templates import (
    build_confirmation_message,
    build_whatsapp_link,
)
from app.domain.sales.session_state_machine import SessionStatus
from app.models.session import Session
from app.services.session_service import SessionService


def test_messaging_templates():
    """Testa geração do template de lembrete D-1 e do link wa.me."""
    msg = build_confirmation_message("Maria Clara da Silva", "Limpeza de Pele", "14:30")
    assert "Oi Maria!" in msg
    assert "Limpeza de Pele" in msg
    assert "14:30" in msg

    # Com telefone 11 dígitos
    link = build_whatsapp_link("(11) 98765-4321", msg)
    assert link is not None
    assert link.startswith("https://wa.me/5511987654321?text=")

    # Sem telefone
    assert build_whatsapp_link(None, msg) is None
    assert build_whatsapp_link("", msg) is None


def test_session_confirm_success():
    """Testa confirmação de sessão em status SCHEDULED."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        professional_id=uuid4(),
        sale_item_id=uuid4(),
        sequence_number=1,
        status=SessionStatus.SCHEDULED,
        confirmed_at=None,
    )

    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = mock_session

    svc = SessionService(
        session_repo=mock_repo,
        sale_item_repo=MagicMock(),
        sale_repo=MagicMock(),
        procedure_repo=MagicMock(),
        patient_repo=MagicMock(),
        booking_repo=MagicMock(),
        return_opportunity_repo=MagicMock(),
        professional_repo=MagicMock(),
    )

    confirmed = svc.confirm(session_id)
    assert confirmed.confirmed_at is not None
    mock_repo.flush.assert_called_once()


def test_session_confirm_invalid_status_raises_error():
    """Tentar confirmar uma sessão que não está SCHEDULED deve falhar com ValueError."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        professional_id=uuid4(),
        sale_item_id=uuid4(),
        sequence_number=1,
        status=SessionStatus.COMPLETED,
        confirmed_at=None,
    )

    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = mock_session

    svc = SessionService(
        session_repo=mock_repo,
        sale_item_repo=MagicMock(),
        sale_repo=MagicMock(),
        procedure_repo=MagicMock(),
        patient_repo=MagicMock(),
        booking_repo=MagicMock(),
        return_opportunity_repo=MagicMock(),
        professional_repo=MagicMock(),
    )

    with pytest.raises(ValueError, match="Apenas sessões agendadas podem ser confirmadas"):
        svc.confirm(session_id)


def test_dashboard_no_show_metrics():
    """Testa cálculo de no_show_count e no_show_rate no build_dashboard."""
    today = date(2026, 8, 31)

    # 4 concluídas + 1 no-show -> total 5 atendimentos agendados, taxa = 1/5 = 0.2000 (20%)
    res = build_dashboard(
        sales=[
            SaleForDashboard(
                gross_amount=Decimal("1000.00"),
                net_profit=Decimal("600.00"),
                expected_receipt_date=None,
                sold_at=today,
            )
        ],
        session_count=4,
        no_show_count=1,
        fixed_expenses=[FixedExpenseForDashboard(amount=Decimal("100.00"), periodicity="MONTHLY")],
        period_kind=PeriodKind.MONTH,
        today=today,
        date_to=today,
        has_any_sale_ever=True,
    )

    assert res.no_show_count == 1
    assert res.no_show_rate == Decimal("0.2000")
    assert res.session_count == 4
