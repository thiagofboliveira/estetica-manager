from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.sales.session_state_machine import SessionStatus
from app.models.sale import Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.session import Session
from app.repositories.booking import BookingRepository
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.patient import PatientRepository
from app.repositories.payment_fee_rule import PaymentFeeRuleRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.services.sale_service import SaleService


@pytest.fixture
def sale_service_mocks():
    sale_repo = MagicMock(spec=SaleRepository)
    sale_item_repo = MagicMock(spec=SaleItemRepository)
    session_repo = MagicMock(spec=SessionRepository)
    procedure_repo = MagicMock(spec=ProcedureRepository)
    patient_repo = MagicMock(spec=PatientRepository)
    fin_repo = MagicMock(spec=FinancialSettingsRepository)
    fee_repo = MagicMock(spec=PaymentFeeRuleRepository)
    prof_repo = MagicMock(spec=ProfessionalRepository)
    booking_repo = MagicMock(spec=BookingRepository)
    return_opp_repo = MagicMock(spec=ReturnOpportunityRepository)

    svc = SaleService(
        sale_repo=sale_repo,
        sale_item_repo=sale_item_repo,
        session_repo=session_repo,
        procedure_repo=procedure_repo,
        patient_repo=patient_repo,
        financial_settings_repo=fin_repo,
        payment_fee_rule_repo=fee_repo,
        professional_repo=prof_repo,
        booking_repo=booking_repo,
        return_opportunity_repo=return_opp_repo,
    )
    return {
        "svc": svc,
        "sale_repo": sale_repo,
        "sale_item_repo": sale_item_repo,
        "session_repo": session_repo,
    }


def test_cancel_sale_cancels_remaining_sessions(sale_service_mocks):
    mocks = sale_service_mocks
    svc = mocks["svc"]

    sale_id = uuid4()
    item_id = uuid4()

    sale = Sale(
        id=sale_id,
        patient_id=uuid4(),
        type=SaleType.PACKAGE,
        status=SaleStatus.ACTIVE,
        notes="Venda teste",
    )
    item = SaleItem(id=item_id, sale_id=sale_id, procedure_id=uuid4(), quantity=2)
    s1 = Session(
        id=uuid4(),
        sale_item_id=item_id,
        sequence_number=1,
        status=SessionStatus.COMPLETED,
    )
    s2 = Session(
        id=uuid4(),
        sale_item_id=item_id,
        sequence_number=2,
        status=SessionStatus.PENDING,
    )

    mocks["sale_repo"].get.return_value = sale
    mocks["sale_item_repo"].list_for_sale.return_value = [item]
    mocks["session_repo"].list_for_sale_item.return_value = [s1, s2]

    cancelled = svc.cancel(sale_id, reason="Desistência do cliente")

    assert cancelled.status == SaleStatus.CANCELLED
    assert "Cancelada: Desistência do cliente" in cancelled.notes
    assert s1.status == SessionStatus.COMPLETED  # sessão já feita não muda
    assert s2.status == SessionStatus.CANCELLED  # sessão pendente é cancelada
    mocks["sale_repo"].flush.assert_called_once()


def test_refund_sale_refunds_and_cancels_pending(sale_service_mocks):
    mocks = sale_service_mocks
    svc = mocks["svc"]

    sale_id = uuid4()
    item_id = uuid4()

    sale = Sale(
        id=sale_id,
        patient_id=uuid4(),
        type=SaleType.SINGLE,
        status=SaleStatus.ACTIVE,
    )
    item = SaleItem(id=item_id, sale_id=sale_id, procedure_id=uuid4(), quantity=1)
    s1 = Session(
        id=uuid4(),
        sale_item_id=item_id,
        sequence_number=1,
        status=SessionStatus.SCHEDULED,
    )

    mocks["sale_repo"].get.return_value = sale
    mocks["sale_item_repo"].list_for_sale.return_value = [item]
    mocks["session_repo"].list_for_sale_item.return_value = [s1]

    refunded = svc.refund(sale_id, reason="Erro no valor cobrado")

    assert refunded.status == SaleStatus.REFUNDED
    assert "Estornada: Erro no valor cobrado" in refunded.notes
    assert s1.status == SessionStatus.CANCELLED
    mocks["sale_repo"].flush.assert_called_once()
