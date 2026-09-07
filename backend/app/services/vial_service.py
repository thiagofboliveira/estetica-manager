from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.models.vial import OpenVial, VialStatus
from app.repositories.procedure import ProcedureRepository
from app.repositories.vial_repository import OpenVialRepository
from app.schemas.vial import OpenVialConsume, OpenVialCreate, OpenVialUpdate


class VialNotFoundError(Exception):
    pass


class InsufficientVialUnitsError(Exception):
    pass


class VialService:
    def __init__(
        self,
        repo: OpenVialRepository,
        procedure_repo: ProcedureRepository | None = None,
    ) -> None:
        self._repo = repo
        self._procedure_repo = procedure_repo

    def create(self, dto: OpenVialCreate) -> OpenVial:
        opened_at = dto.opened_at or datetime.now(UTC)
        expires_at = dto.expires_at or (opened_at + timedelta(days=dto.validity_days))

        vial = OpenVial(
            procedure_id=dto.procedure_id,
            medication_name=dto.medication_name,
            lot_number=dto.lot_number,
            total_units=dto.total_units,
            used_units=dto.used_units,
            unit_measure=dto.unit_measure,
            cost_price=dto.cost_price,
            opened_at=opened_at,
            expires_at=expires_at,
            status=VialStatus.OPEN,
            notes=dto.notes,
        )
        saved = self._repo.add(vial)
        return saved

    def list_active(self) -> list[OpenVial]:
        vials = self._repo.list_active()
        now = datetime.now(UTC)
        for v in vials:
            if v.expires_at and v.expires_at < now and v.status == VialStatus.OPEN:
                v.status = VialStatus.EXPIRED
        self._repo._session.flush()
        return vials

    def list_all(self, limit: int = 50) -> list[OpenVial]:
        return self._repo.list_recent(limit=limit)

    def get(self, vial_id: UUID) -> OpenVial:
        vial = self._repo.get_with_procedure(vial_id)
        if not vial or not vial.is_active:
            raise VialNotFoundError(f"Frasco {vial_id} não encontrado")
        return vial

    def consume(self, vial_id: UUID, dto: OpenVialConsume) -> OpenVial:
        vial = self.get(vial_id)
        if vial.status != VialStatus.OPEN:
            raise ValueError("Apenas frascos com status ABERTO podem ser consumidos")

        remaining = vial.remaining_units
        if dto.units > remaining:
            raise InsufficientVialUnitsError(
                f"Quantidade solicitada ({dto.units}) excede o saldo restante no frasco ({remaining})"
            )

        vial.used_units += dto.units
        if dto.notes:
            vial.notes = (
                f"{vial.notes}\n[Aplicação]: {dto.units}{vial.unit_measure} - {dto.notes}"
                if vial.notes
                else f"[Aplicação]: {dto.units}{vial.unit_measure} - {dto.notes}"
            )

        if vial.used_units >= vial.total_units:
            vial.status = VialStatus.FINISHED

        self._repo._session.flush()
        return vial

    def finish(self, vial_id: UUID) -> OpenVial:
        vial = self.get(vial_id)
        vial.status = VialStatus.FINISHED
        self._repo._session.flush()
        return vial

    def update(self, vial_id: UUID, dto: OpenVialUpdate) -> OpenVial:
        vial = self.get(vial_id)
        if dto.medication_name is not None:
            vial.medication_name = dto.medication_name
        if dto.lot_number is not None:
            vial.lot_number = dto.lot_number
        if dto.status is not None:
            vial.status = dto.status
        if dto.cost_price is not None:
            vial.cost_price = dto.cost_price
        if dto.notes is not None:
            vial.notes = dto.notes

        self._repo._session.flush()
        return vial

    def delete(self, vial_id: UUID) -> None:
        vial = self.get(vial_id)
        vial.is_active = False
        self._repo._session.flush()
