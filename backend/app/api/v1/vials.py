from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import VialSvc
from app.models.vial import OpenVial
from app.schemas.vial import (
    OpenVialConsume,
    OpenVialCreate,
    OpenVialOut,
    OpenVialUpdate,
)
from app.services.vial_service import (
    InsufficientVialUnitsError,
    VialNotFoundError,
)

router = APIRouter(prefix="/vials", tags=["vials"])


def _to_out(vial: OpenVial) -> OpenVialOut:
    remaining = vial.remaining_units
    cost_per_unit = None
    estimated_loss = None
    if vial.cost_price and vial.total_units > 0:
        cost_per_unit = (vial.cost_price / vial.total_units).quantize(Decimal("0.01"))
        estimated_loss = (remaining * cost_per_unit).quantize(Decimal("0.01"))

    now = datetime.now(UTC)
    is_exp = now > vial.expires_at if vial.expires_at else False
    days_rem = 0
    if vial.expires_at and not is_exp:
        days_rem = max(0, (vial.expires_at - now).days)

    return OpenVialOut(
        id=vial.id,
        medication_name=vial.medication_name,
        lot_number=vial.lot_number,
        total_units=vial.total_units,
        used_units=vial.used_units,
        remaining_units=remaining,
        unit_measure=vial.unit_measure,
        cost_price=vial.cost_price,
        cost_per_unit=cost_per_unit,
        estimated_loss_risk=estimated_loss,
        opened_at=vial.opened_at,
        expires_at=vial.expires_at,
        days_remaining=days_rem,
        is_expired=is_exp,
        status=vial.status,
        procedure_id=vial.procedure_id,
        procedure_name=vial.procedure.name if vial.procedure else None,
        notes=vial.notes,
        created_at=vial.created_at,
    )


@router.get("", response_model=list[OpenVialOut])
def list_vials(
    svc: VialSvc,
    include_all: bool = Query(default=False, description="Se true, inclui finalizados e descartados"),
) -> list[OpenVialOut]:
    vials = svc.list_all() if include_all else svc.list_active()
    return [_to_out(v) for v in vials]


@router.post("", response_model=OpenVialOut, status_code=status.HTTP_201_CREATED)
def create_vial(
    payload: OpenVialCreate,
    svc: VialSvc,
) -> OpenVialOut:
    vial = svc.create(payload)
    return _to_out(vial)


@router.get("/{vial_id}", response_model=OpenVialOut)
def get_vial(
    vial_id: UUID,
    svc: VialSvc,
) -> OpenVialOut:
    try:
        vial = svc.get(vial_id)
        return _to_out(vial)
    except VialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frasco não encontrado",
        ) from exc


@router.post("/{vial_id}/consume", response_model=OpenVialOut)
def consume_vial_units(
    vial_id: UUID,
    payload: OpenVialConsume,
    svc: VialSvc,
) -> OpenVialOut:
    try:
        vial = svc.consume(vial_id, payload)
        return _to_out(vial)
    except VialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frasco não encontrado",
        ) from exc
    except InsufficientVialUnitsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{vial_id}/finish", response_model=OpenVialOut)
def finish_vial(
    vial_id: UUID,
    svc: VialSvc,
) -> OpenVialOut:
    try:
        vial = svc.finish(vial_id)
        return _to_out(vial)
    except VialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frasco não encontrado",
        ) from exc


@router.patch("/{vial_id}", response_model=OpenVialOut)
def update_vial(
    vial_id: UUID,
    payload: OpenVialUpdate,
    svc: VialSvc,
) -> OpenVialOut:
    try:
        vial = svc.update(vial_id, payload)
        return _to_out(vial)
    except VialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frasco não encontrado",
        ) from exc


@router.delete("/{vial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vial(
    vial_id: UUID,
    svc: VialSvc,
) -> None:
    try:
        svc.delete(vial_id)
    except VialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frasco não encontrado",
        ) from exc
