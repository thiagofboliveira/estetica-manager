from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.procedure import Modality, Procedure, ProcedureType, SessionPlan
from app.models.procedure_supply import ProcedureSupply
from app.models.sale import Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.session import Session, SessionStatus
from app.models.supply import MovementType, Supply, SupplyCategory, SupplyMovement
from app.schemas.procedure import ProcedureCreate, ProcedureSupplyItem, ProcedureUpdate
from app.schemas.session import SessionUpdate
from app.services.procedure_service import ProcedureService
from app.services.session_service import SessionService


def test_procedure_service_create_and_update_with_supplies():
    repo = MagicMock()
    prof_id = uuid4()
    repo._professional_id = prof_id
    repo._session = MagicMock()

    proc_id = uuid4()
    created_proc = Procedure(
        id=proc_id,
        professional_id=prof_id,
        name="Toxina Botulínica Testa",
        type=ProcedureType.SERVICE,
        price=Decimal("800.00"),
        estimated_cost=Decimal("200.00"),
        is_invasive=True,
        session_plan=SessionPlan.SINGLE,
    )
    repo.add.return_value = created_proc
    repo.get.return_value = created_proc

    svc = ProcedureService(repo)

    supply_id_1 = uuid4()
    supply_id_2 = uuid4()
    dto = ProcedureCreate(
        name="Toxina Botulínica Testa",
        type=ProcedureType.SERVICE,
        price="800.00",
        estimated_cost="200.00",
        supplies=[
            ProcedureSupplyItem(supply_id=supply_id_1, quantity=Decimal("50.00")),
            ProcedureSupplyItem(supply_id=supply_id_2, quantity=Decimal("1.00")),
        ],
    )

    result = svc.create(dto)
    assert result.name == "Toxina Botulínica Testa"
    assert repo.add.called
    assert repo._session.add.call_count == 2


def test_session_completion_consumes_supplies_and_calculates_real_cost():
    session_repo = MagicMock()
    sale_item_repo = MagicMock()
    sale_repo = MagicMock()
    procedure_repo = MagicMock()
    patient_repo = MagicMock()
    booking_repo = MagicMock()

    db_session = MagicMock()
    session_repo._session = db_session
    prof_id = uuid4()
    session_repo._professional_id = prof_id

    # Supply in stock: 100 UI, cost R$ 3.00 each
    supply_id = uuid4()
    supply = Supply(
        id=supply_id,
        professional_id=prof_id,
        name="Botox 100U",
        category=SupplyCategory.INJECTABLE,
        current_stock=Decimal("100.00"),
        unit_measure="UI",
        cost_price=Decimal("3.00"),
        is_active=True,
    )

    # Procedure with 50 UI in recipe
    proc_id = uuid4()
    proc = Procedure(
        id=proc_id,
        professional_id=prof_id,
        name="Botox Glabella",
        type=ProcedureType.SERVICE,
        price=Decimal("600.00"),
        estimated_cost=Decimal("150.00"),
    )
    proc_supply = ProcedureSupply(
        procedure_id=proc_id,
        supply_id=supply_id,
        quantity=Decimal("50.00"),
        professional_id=prof_id,
    )
    proc_supply.supply = supply
    proc.supplies = [proc_supply]

    # Sale and item
    sale_id = uuid4()
    sale_item_id = uuid4()
    sale = Sale(
        id=sale_id,
        professional_id=prof_id,
        patient_id=uuid4(),
        type=SaleType.SINGLE,
        status=SaleStatus.ACTIVE,
        cost_realized=Decimal("0.00"),
    )
    sale_item = SaleItem(
        id=sale_item_id,
        sale_id=sale_id,
        procedure_id=proc_id,
        quantity=1,
        unit_price=Decimal("600.00"),
        unit_cost_estimated=Decimal("150.00"),
        professional_id=prof_id,
    )

    # Session
    sess_id = uuid4()
    session = Session(
        id=sess_id,
        professional_id=prof_id,
        sale_item_id=sale_item_id,
        sequence_number=1,
        status=SessionStatus.SCHEDULED,
        modality=Modality.IN_PERSON,
        cost_override=None,
    )

    session_repo.get_by_id.return_value = session
    sale_item_repo.get.return_value = sale_item
    procedure_repo.get.return_value = proc
    sale_repo.get.return_value = sale
    sale_item_repo.list_for_sale.return_value = [sale_item]
    session_repo.list_for_sale_item.return_value = [session]
    db_session.get.return_value = supply

    svc = SessionService(
        session_repo=session_repo,
        sale_item_repo=sale_item_repo,
        sale_repo=sale_repo,
        procedure_repo=procedure_repo,
        patient_repo=patient_repo,
        booking_repo=booking_repo,
    )

    # Complete the session
    updated_session, _ = svc.update(sess_id, SessionUpdate(status=SessionStatus.COMPLETED))

    # Assert stock was deducted: 100 - 50 = 50
    assert supply.current_stock == Decimal("50.00")

    # Assert movement was added
    assert db_session.add.called
    added_movement = db_session.add.call_args[0][0]
    assert isinstance(added_movement, SupplyMovement)
    assert added_movement.movement_type == MovementType.EXIT
    assert added_movement.quantity == Decimal("50.00")
    assert added_movement.unit_price == Decimal("3.00")

    # Assert real cost was calculated: 50 * 3.00 = 150.00
    assert updated_session.cost_override == Decimal("150.00")
    assert sale.cost_realized == Decimal("150.00")
