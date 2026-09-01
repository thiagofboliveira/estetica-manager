from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.sales.session_state_machine import (
    InvalidSessionTransitionError,
    SessionStatus,
)
from app.models.procedure import Modality
from app.models.return_opportunity import ReturnOpportunity
from app.models.sale import Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.session import Session
from app.repositories.booking import BookingRepository
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.schemas.session import SessionUpdate
from app.services.session_service import SessionService


@pytest.fixture
def session_service_mocks():
    prof_id = uuid4()
    session_repo = MagicMock(spec=SessionRepository)
    session_repo._professional_id = prof_id
    sale_item_repo = MagicMock(spec=SaleItemRepository)
    sale_repo = MagicMock(spec=SaleRepository)
    procedure_repo = MagicMock(spec=ProcedureRepository)
    patient_repo = MagicMock(spec=PatientRepository)
    booking_repo = MagicMock(spec=BookingRepository)
    return_opportunity_repo = MagicMock(spec=ReturnOpportunityRepository)
    professional_repo = MagicMock(spec=ProfessionalRepository)

    svc = SessionService(
        session_repo=session_repo,
        sale_item_repo=sale_item_repo,
        sale_repo=sale_repo,
        procedure_repo=procedure_repo,
        patient_repo=patient_repo,
        booking_repo=booking_repo,
        return_opportunity_repo=return_opportunity_repo,
        professional_repo=professional_repo,
    )
    return {
        "svc": svc,
        "session_repo": session_repo,
        "sale_item_repo": sale_item_repo,
        "sale_repo": sale_repo,
        "booking_repo": booking_repo,
        "return_opportunity_repo": return_opportunity_repo,
    }


def test_session_schedule_with_conflict_warning(session_service_mocks):
    mocks = session_service_mocks
    svc = mocks["svc"]

    session_id = uuid4()
    session = Session(
        id=session_id,
        professional_id=uuid4(),
        sale_item_id=uuid4(),
        sequence_number=1,
        status=SessionStatus.PENDING,
        modality=Modality.IN_PERSON,
    )
    mocks["session_repo"].get_by_id.return_value = session
    # Simula conflito de horário
    conflito = Session(
        id=uuid4(), status=SessionStatus.SCHEDULED, modality=Modality.IN_PERSON
    )
    mocks["session_repo"].find_conflicts.return_value = [conflito]
    mocks["booking_repo"].find_conflicts.return_value = []

    sched_dt = datetime(2026, 9, 1, 14, 0, tzinfo=UTC)
    dto = SessionUpdate(scheduled_at=sched_dt)

    updated, warnings = svc.update(session_id, dto)

    assert updated.status == SessionStatus.SCHEDULED
    assert updated.scheduled_at == sched_dt
    assert len(warnings) == 1
    assert "Já existe atendimento agendado" in warnings[0]


def test_session_completed_triggers_return_opportunity_on_last_session(
    session_service_mocks,
):
    mocks = session_service_mocks
    svc = mocks["svc"]

    session_id = uuid4()
    sale_item_id = uuid4()
    sale_id = uuid4()
    patient_id = uuid4()
    procedure_id = uuid4()

    session = Session(
        id=session_id,
        professional_id=uuid4(),
        sale_item_id=sale_item_id,
        sequence_number=1,
        status=SessionStatus.SCHEDULED,
        modality=Modality.IN_PERSON,
    )
    mocks["session_repo"].get_by_id.return_value = session
    mocks["session_repo"].list_for_sale_item.return_value = [session]

    sale_item = SaleItem(
        id=sale_item_id,
        sale_id=sale_id,
        procedure_id=procedure_id,
        quantity=1,
        unit_price=Decimal("1000.00"),
        unit_cost_estimated=Decimal("350.00"),
        return_interval_applied=180,
    )
    mocks["sale_item_repo"].get.return_value = sale_item

    sale = Sale(
        id=sale_id,
        patient_id=patient_id,
        type=SaleType.SINGLE,
        status=SaleStatus.ACTIVE,
    )
    mocks["sale_repo"].get.return_value = sale
    mocks[
        "return_opportunity_repo"
    ].find_open_for_patient_and_procedure.return_value = []

    dto = SessionUpdate(status=SessionStatus.COMPLETED)
    updated, warnings = svc.update(session_id, dto)

    assert updated.status == SessionStatus.COMPLETED
    assert updated.completed_at is not None
    mocks["return_opportunity_repo"].add.assert_called_once()
    opp_created = mocks["return_opportunity_repo"].add.call_args[0][0]
    assert isinstance(opp_created, ReturnOpportunity)
    assert opp_created.patient_id == patient_id
    assert opp_created.procedure_id == procedure_id
    assert opp_created.source_sale_item_id == sale_item_id


def test_session_invalid_transition_raises_error(session_service_mocks):
    mocks = session_service_mocks
    svc = mocks["svc"]

    session_id = uuid4()
    session = Session(
        id=session_id,
        professional_id=uuid4(),
        sale_item_id=uuid4(),
        sequence_number=1,
        status=SessionStatus.COMPLETED,
        modality=Modality.IN_PERSON,
    )
    mocks["session_repo"].get_by_id.return_value = session

    # Transição de COMPLETED -> SCHEDULED é proibida pela máquina de estados
    dto = SessionUpdate(status=SessionStatus.SCHEDULED)
    with pytest.raises(InvalidSessionTransitionError):
        svc.update(session_id, dto)
