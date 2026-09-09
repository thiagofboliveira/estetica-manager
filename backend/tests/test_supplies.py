from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.supply import MovementType, Supply, SupplyCategory, SupplyMovement
from app.repositories.supply_repository import SupplyRepository
from app.schemas.supply import SupplyCreate, SupplyMovementCreate, SupplyUpdate
from app.services.supply_service import (
    InsufficientStockError,
    SupplyNotFoundError,
    SupplyService,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def mock_repo():
    return MagicMock(spec=SupplyRepository)


def test_create_supply_with_initial_stock(mock_session, mock_repo):
    prof_id = uuid4()
    svc = SupplyService(session=mock_session, professional_id=prof_id, supply_repo=mock_repo)

    payload = SupplyCreate(
        name="Restylane Defyne 1ml",
        category=SupplyCategory.FILLER,
        brand="Galderma",
        unit_measure="SERINGA",
        current_stock=Decimal("5.00"),
        min_stock_alert=Decimal("2.00"),
        cost_price=Decimal("450.00"),
        notes="Preenchedor labial e mento",
    )

    supply = svc.create(payload)

    assert supply.name == "Restylane Defyne 1ml"
    assert supply.category == SupplyCategory.FILLER
    assert supply.current_stock == Decimal("5.00")
    assert supply.unit_measure == "SERINGA"
    mock_repo.add.assert_called_once()
    mock_repo.add_movement.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_not_called()


def test_supply_movement_entry_and_exit(mock_session, mock_repo):
    prof_id = uuid4()
    supply_id = uuid4()

    mock_supply = Supply(
        id=supply_id,
        professional_id=prof_id,
        name="Botox 100U",
        category=SupplyCategory.INJECTABLE,
        brand="Allergan",
        unit_measure="FRASCO",
        current_stock=Decimal("3.00"),
        min_stock_alert=Decimal("1.00"),
        cost_price=Decimal("850.00"),
        is_active=True,
    )
    mock_repo.get_by_id.return_value = mock_supply

    svc = SupplyService(session=mock_session, professional_id=prof_id, supply_repo=mock_repo)

    # 1. Entrada de 2 frascos
    supply, mov1 = svc.record_movement(
        supply_id,
        SupplyMovementCreate(
            movement_type=MovementType.ENTRY,
            quantity=Decimal("2.00"),
            unit_price=Decimal("850.00"),
            notes="Compra NF 4589",
        ),
    )
    assert supply.current_stock == Decimal("5.00")

    # 2. Saída de 1 frasco
    supply, mov2 = svc.record_movement(
        supply_id,
        SupplyMovementCreate(
            movement_type=MovementType.EXIT,
            quantity=Decimal("1.00"),
            notes="Abertura para aplicação em consultório",
        ),
    )
    assert supply.current_stock == Decimal("4.00")


def test_supply_insufficient_stock_error(mock_session, mock_repo):
    prof_id = uuid4()
    supply_id = uuid4()

    mock_supply = Supply(
        id=supply_id,
        professional_id=prof_id,
        name="Cânula 22G 50mm",
        category=SupplyCategory.CONSUMABLE,
        unit_measure="UN",
        current_stock=Decimal("2.00"),
        is_active=True,
    )
    mock_repo.get_by_id.return_value = mock_supply

    svc = SupplyService(session=mock_session, professional_id=prof_id, supply_repo=mock_repo)

    with pytest.raises(InsufficientStockError) as exc_info:
        svc.record_movement(
            supply_id,
            SupplyMovementCreate(
                movement_type=MovementType.EXIT,
                quantity=Decimal("5.00"),
            ),
        )

    assert "Estoque insuficiente" in str(exc_info.value)
