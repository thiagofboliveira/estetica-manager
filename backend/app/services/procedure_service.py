from uuid import UUID

from app.core.money import money
from app.domain.catalog.procedure_templates import find_procedure_template
from app.models.procedure import Procedure, ProcedureType, SessionPlan
from app.models.procedure_supply import ProcedureSupply
from app.repositories.procedure import ProcedureRepository
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureFromTemplateCreate,
    ProcedureUpdate,
)


class ProcedureNotFoundError(Exception):
    pass


class ProcedureAlreadyExistsError(Exception):
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
            split_override=money(dto.split_override)
            if dto.split_override is not None
            else None,
            is_invasive=dto.is_invasive,
            session_plan=dto.session_plan,
            image_url=dto.image_url,
        )
        procedure = self._repo.add(procedure)
        self._repo.flush()

        if dto.supplies:
            for item in dto.supplies:
                ps = ProcedureSupply(
                    professional_id=procedure.professional_id,
                    procedure_id=procedure.id,
                    supply_id=item.supply_id,
                    quantity=item.quantity,
                )
                self._repo._session.add(ps)
            self._repo.flush()
            self._repo._session.refresh(procedure)

        return procedure

    def create_from_template(self, dto: ProcedureFromTemplateCreate) -> Procedure:
        """Cria procedimento a partir de template com overrides opcionais (TASK-BACK-S2-19)."""
        template = find_procedure_template(dto.template_id)
        if not template:
            raise ValueError(f"Template '{dto.template_id}' não encontrado.")

        name = dto.name.strip() if dto.name else template.name
        existing = self._repo.find_by_name(name)
        if existing:
            raise ProcedureAlreadyExistsError(
                f"Procedimento '{name}' já está cadastrado."
            )

        price = dto.price if dto.price is not None else str(template.suggested_price)
        estimated_cost = (
            dto.estimated_cost
            if dto.estimated_cost is not None
            else str(template.suggested_cost)
        )
        return_interval_days = (
            dto.return_interval_days
            if dto.return_interval_days is not None
            else template.suggested_return_interval_days
        )

        create_dto = ProcedureCreate(
            name=name,
            type=ProcedureType.SERVICE,
            price=price,
            estimated_cost=estimated_cost,
            return_interval_days=return_interval_days,
            default_modality=dto.default_modality,
            split_override=dto.split_override,
            image_url=dto.image_url,
        )
        return self.create(create_dto)

    def get(self, procedure_id: UUID) -> Procedure:
        procedure = self._repo.get(procedure_id)
        if procedure is None:
            raise ProcedureNotFoundError()
        return procedure

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        is_invasive: bool | None = None,
        session_plan: SessionPlan | None = None,
    ) -> list[Procedure]:
        return self._repo.list(
            limit=limit,
            offset=offset,
            is_invasive=is_invasive,
            session_plan=session_plan,
        )

    def count(
        self,
        *,
        is_invasive: bool | None = None,
        session_plan: SessionPlan | None = None,
    ) -> int:
        return self._repo.count(is_invasive=is_invasive, session_plan=session_plan)

    def update(self, procedure_id: UUID, dto: ProcedureUpdate) -> Procedure:
        procedure = self.get(procedure_id)
        data = dto.model_dump(exclude_unset=True)

        supplies_data = data.pop("supplies", None)

        if "price" in data and data["price"] is not None:
            data["price"] = money(data["price"])
        if "estimated_cost" in data and data["estimated_cost"] is not None:
            data["estimated_cost"] = money(data["estimated_cost"])
        if "split_override" in data and data["split_override"] is not None:
            data["split_override"] = money(data["split_override"])

        for field, value in data.items():
            setattr(procedure, field, value)

        if supplies_data is not None:
            # Sincroniza insumos da ficha técnica
            for old_ps in list(procedure.supplies):
                self._repo._session.delete(old_ps)
            self._repo.flush()

            for item in (dto.supplies or []):
                ps = ProcedureSupply(
                    professional_id=procedure.professional_id,
                    procedure_id=procedure.id,
                    supply_id=item.supply_id,
                    quantity=item.quantity,
                )
                self._repo._session.add(ps)
            self._repo.flush()
            self._repo._session.refresh(procedure)

        self._repo.flush()
        return procedure

    def deactivate(self, procedure_id: UUID) -> None:
        procedure = self.get(procedure_id)
        procedure.is_active = False
        self._repo.flush()
