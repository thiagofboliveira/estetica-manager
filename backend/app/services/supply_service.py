from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.supply import MovementType, Supply, SupplyCategory, SupplyMovement
from app.repositories.supply_repository import SupplyRepository
from app.schemas.supply import SupplyCreate, SupplyMovementCreate, SupplyUpdate


class SupplyNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class SupplyService:
    def __init__(
        self,
        session: Session,
        professional_id: UUID,
        clinic_id: UUID | None = None,
        supply_repo: SupplyRepository | None = None,
    ):
        self._session = session
        self._professional_id = professional_id
        self._clinic_id = clinic_id
        self._repo = supply_repo or SupplyRepository(session, professional_id)

    def list_supplies(
        self,
        category: SupplyCategory | None = None,
        search: str | None = None,
    ) -> list[Supply]:
        return self._repo.list_all_active(category=category, search=search)

    def get(self, supply_id: UUID) -> Supply:
        supply = self._repo.get_by_id(supply_id)
        if not supply:
            raise SupplyNotFoundError(f"Insumo {supply_id} não encontrado")
        return supply

    def create(self, payload: SupplyCreate) -> Supply:
        supply = Supply(
            professional_id=self._professional_id,
            clinic_id=self._clinic_id,
            name=payload.name.strip(),
            category=payload.category,
            brand=payload.brand.strip() if payload.brand else None,
            unit_measure=payload.unit_measure.strip().upper(),
            current_stock=payload.current_stock,
            min_stock_alert=payload.min_stock_alert,
            cost_price=payload.cost_price,
            notes=payload.notes.strip() if payload.notes else None,
            is_active=True,
        )
        self._repo.add(supply)

        # Se começou com estoque inicial > 0, registra a movimentação de entrada inicial
        if payload.current_stock > Decimal("0.00"):
            initial_movement = SupplyMovement(
                professional_id=self._professional_id,
                clinic_id=self._clinic_id,
                supply_id=supply.id,
                movement_type=MovementType.ENTRY,
                quantity=payload.current_stock,
                unit_price=payload.cost_price,
                notes="Estoque inicial de cadastro",
            )
            self._repo.add_movement(initial_movement)

        self._session.flush()
        self._session.refresh(supply)
        return supply

    def update(self, supply_id: UUID, payload: SupplyUpdate) -> Supply:
        supply = self.get(supply_id)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data and data["name"]:
            supply.name = data["name"].strip()
        if "category" in data and data["category"]:
            supply.category = data["category"]
        if "brand" in data:
            supply.brand = data["brand"].strip() if data["brand"] else None
        if "unit_measure" in data and data["unit_measure"]:
            supply.unit_measure = data["unit_measure"].strip().upper()
        if "current_stock" in data and data["current_stock"] is not None:
            supply.current_stock = data["current_stock"]
        if "min_stock_alert" in data:
            supply.min_stock_alert = data["min_stock_alert"]
        if "cost_price" in data:
            supply.cost_price = data["cost_price"]
        if "notes" in data:
            supply.notes = data["notes"].strip() if data["notes"] else None
        if "is_active" in data and data["is_active"] is not None:
            supply.is_active = data["is_active"]

        self._session.flush()
        self._session.refresh(supply)
        return supply

    def delete(self, supply_id: UUID) -> None:
        supply = self.get(supply_id)
        supply.is_active = False
        self._session.flush()

    def record_movement(
        self,
        supply_id: UUID,
        payload: SupplyMovementCreate,
    ) -> tuple[Supply, SupplyMovement]:
        supply = self.get(supply_id)
        qty = payload.quantity

        if payload.movement_type == MovementType.ENTRY:
            supply.current_stock += qty
            if payload.unit_price is not None and payload.unit_price > 0:
                supply.cost_price = payload.unit_price
        elif payload.movement_type in (MovementType.EXIT, MovementType.LOSS):
            if supply.current_stock < qty:
                raise InsufficientStockError(
                    f"Estoque insuficiente. Saldo disponível: {supply.current_stock} {supply.unit_measure}."
                )
            supply.current_stock -= qty
        elif payload.movement_type == MovementType.ADJUSTMENT:
            supply.current_stock = qty

        movement = SupplyMovement(
            professional_id=self._professional_id,
            clinic_id=self._clinic_id,
            supply_id=supply.id,
            movement_type=payload.movement_type,
            quantity=qty,
            unit_price=payload.unit_price,
            notes=payload.notes.strip() if payload.notes else None,
        )
        self._repo.add_movement(movement)
        self._session.flush()
        self._session.refresh(supply)
        self._session.refresh(movement)
        return supply, movement

    def list_movements(
        self,
        supply_id: UUID | None = None,
        limit: int = 100,
    ) -> list[SupplyMovement]:
        return self._repo.list_movements(supply_id=supply_id, limit=limit)
