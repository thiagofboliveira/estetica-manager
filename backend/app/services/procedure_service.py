from uuid import UUID

from app.core.money import money
from app.domain.catalog.procedure_templates import (
    find_procedure_template,
    list_procedure_templates,
)
from app.models.procedure import Procedure, ProcedureType
from app.repositories.procedure import ProcedureRepository
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureFromTemplateCreate,
    ProcedureTemplateOut,
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
        )
        return self._repo.add(procedure)

    def list_templates(self) -> list[ProcedureTemplateOut]:
        """Retorna templates de procedimentos do catálogo de domínio (EPIC-S2-04, TASK-BACK-S2-17)."""
        templates = list_procedure_templates()
        return [
            ProcedureTemplateOut(
                template_id=t.template_id,
                name=t.name,
                type=t.type,
                suggested_price=t.suggested_price,
                suggested_cost=t.suggested_cost,
                suggested_return_interval_days=t.suggested_return_interval_days,
                category=t.category,
                is_suggested=t.is_suggested,
            )
            for t in templates
        ]

    def create_from_template(self, dto: ProcedureFromTemplateCreate) -> Procedure:
        """Cria procedimento a partir de template com overrides opcionais (TASK-BACK-S2-19)."""
        template = find_procedure_template(dto.template_id)
        if not template:
            raise ValueError(f"Template '{dto.template_id}' não encontrado.")

        name = dto.name.strip() if dto.name else template.name
        existing = self._repo.find_by_name(name)
        if existing:
            raise ProcedureAlreadyExistsError(f"Procedimento '{name}' já está cadastrado.")

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
        )
        return self.create(create_dto)

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
