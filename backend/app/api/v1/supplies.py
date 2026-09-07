from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SupplySvc
from app.models.supply import Supply, SupplyCategory, SupplyMovement
from app.schemas.supply import (
    SupplyCreate,
    SupplyMovementCreate,
    SupplyMovementOut,
    SupplyOut,
    SupplyUpdate,
)
from app.services.supply_service import (
    InsufficientStockError,
    SupplyNotFoundError,
)

router = APIRouter(prefix="/supplies", tags=["supplies"])


def _to_supply_out(supply: Supply) -> SupplyOut:
    return SupplyOut(
        id=supply.id,
        name=supply.name,
        category=supply.category,
        brand=supply.brand,
        unit_measure=supply.unit_measure,
        current_stock=supply.current_stock,
        min_stock_alert=supply.min_stock_alert,
        cost_price=supply.cost_price,
        notes=supply.notes,
        is_active=supply.is_active,
        is_low_stock=supply.is_low_stock,
        created_at=supply.created_at,
        updated_at=supply.updated_at,
    )


def _to_movement_out(movement: SupplyMovement) -> SupplyMovementOut:
    return SupplyMovementOut(
        id=movement.id,
        supply_id=movement.supply_id,
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        unit_price=movement.unit_price,
        notes=movement.notes,
        created_at=movement.created_at,
    )


@router.get("", response_model=list[SupplyOut])
def list_supplies(
    svc: SupplySvc,
    category: SupplyCategory | None = Query(default=None),
    search: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
) -> list[SupplyOut]:
    supplies = svc.list_supplies(category=category, search=search)
    if low_stock_only:
        supplies = [s for s in supplies if s.is_low_stock]
    return [_to_supply_out(s) for s in supplies]


@router.post("", response_model=SupplyOut, status_code=status.HTTP_201_CREATED)
def create_supply(
    payload: SupplyCreate,
    svc: SupplySvc,
) -> SupplyOut:
    supply = svc.create(payload)
    return _to_supply_out(supply)


@router.get("/movements/recent", response_model=list[SupplyMovementOut])
def list_recent_movements(
    svc: SupplySvc,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[SupplyMovementOut]:
    movements = svc.list_movements(limit=limit)
    return [_to_movement_out(m) for m in movements]


@router.get("/{supply_id}", response_model=SupplyOut)
def get_supply(
    supply_id: UUID,
    svc: SupplySvc,
) -> SupplyOut:
    try:
        supply = svc.get(supply_id)
        return _to_supply_out(supply)
    except SupplyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo não encontrado",
        ) from exc


@router.patch("/{supply_id}", response_model=SupplyOut)
def update_supply(
    supply_id: UUID,
    payload: SupplyUpdate,
    svc: SupplySvc,
) -> SupplyOut:
    try:
        supply = svc.update(supply_id, payload)
        return _to_supply_out(supply)
    except SupplyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo não encontrado",
        ) from exc


@router.delete("/{supply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supply(
    supply_id: UUID,
    svc: SupplySvc,
) -> None:
    try:
        svc.delete(supply_id)
    except SupplyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo não encontrado",
        ) from exc


@router.post("/{supply_id}/movements", response_model=SupplyMovementOut, status_code=status.HTTP_201_CREATED)
def record_supply_movement(
    supply_id: UUID,
    payload: SupplyMovementCreate,
    svc: SupplySvc,
) -> SupplyMovementOut:
    try:
        _, movement = svc.record_movement(supply_id, payload)
        return _to_movement_out(movement)
    except SupplyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo não encontrado",
        ) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{supply_id}/movements", response_model=list[SupplyMovementOut])
def list_supply_movements(
    supply_id: UUID,
    svc: SupplySvc,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[SupplyMovementOut]:
    try:
        # Garante que o insumo existe
        svc.get(supply_id)
        movements = svc.list_movements(supply_id=supply_id, limit=limit)
        return [_to_movement_out(m) for m in movements]
    except SupplyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo não encontrado",
        ) from exc
