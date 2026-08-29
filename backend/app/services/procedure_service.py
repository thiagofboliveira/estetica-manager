from uuid import UUID

from app.core.money import money
from app.models.procedure import Procedure
from app.repositories.procedure import ProcedureRepository
from app.schemas.procedure import ProcedureCreate, ProcedureUpdate


class ProcedureNotFoundError(Exception):
    pass


class ProcedureService:
    def __init__(self, repo: ProcedureRepository) -> None:
        self._repo = repo

    def create(self, dto: ProcedureCreate) -> Procedure:
        procedure = Procedure(
            name=dto.name,
            type=dto.type,
            price=money(dto.price),
            estimated_cost=money(dto.estimated_cost),
            return_interval_days=dto.return_interval_days,
            default_modality=dto.default_modality,
        )
        return self._repo.add(procedure)

    def get(self, procedure_id: UUID) -> Procedure:
        procedure = self._repo.get(procedure_id)
        if procedure is None:
            raise ProcedureNotFoundError()
        return procedure

    def list(self, *, limit: int = 50, offset: int = 0) -> list[Procedure]:
        return self._repo.list(limit=limit, offset=offset)

    def update(self, procedure_id: UUID, dto: ProcedureUpdate) -> Procedure:
        procedure = self.get(procedure_id)
        data = dto.model_dump(exclude_unset=True)

        if "price" in data and data["price"] is not None:
            data["price"] = money(data["price"])
        if "estimated_cost" in data and data["estimated_cost"] is not None:
            data["estimated_cost"] = money(data["estimated_cost"])

        for field, value in data.items():
            setattr(procedure, field, value)

        self._repo.flush()
        return procedure

    def deactivate(self, procedure_id: UUID) -> None:
        procedure = self.get(procedure_id)
        procedure.is_active = False
        self._repo.flush()
