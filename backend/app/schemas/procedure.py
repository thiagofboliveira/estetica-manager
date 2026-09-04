from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.models.procedure import Modality, ProcedureType, SessionPlan
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class ProcedureCreate(InputSchema):
    name: str = Field(min_length=1)
    type: ProcedureType = ProcedureType.SERVICE
    price: str = Field(description="Valor decimal, ex: '150.00'")
    estimated_cost: str = Field(description="Valor decimal, ex: '40.00'")
    return_interval_days: int | None = Field(default=None, ge=0)
    default_modality: Modality = Modality.IN_PERSON
    split_override: str | None = Field(
        default=None, description="Percentual de comissão customizado, ex: '30.00' (E6 / P1)"
    )
    is_invasive: bool = False
    session_plan: SessionPlan = SessionPlan.SINGLE

    @model_validator(mode="after")
    def _produto_sem_intervalo_de_retorno(self) -> "ProcedureCreate":
        # Produto revendido não tem janela de retorno clínico (MVP v6 §9).
        if self.type is ProcedureType.PRODUCT:
            self.return_interval_days = None
        return self


class ProcedureUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=1)
    type: ProcedureType | None = None
    price: str | None = None
    estimated_cost: str | None = None
    return_interval_days: int | None = Field(default=None, ge=0)
    default_modality: Modality | None = None
    split_override: str | None = None
    is_active: bool | None = None
    is_invasive: bool | None = None
    session_plan: SessionPlan | None = None


class ProcedureOut(OutputSchema):
    id: UUID
    name: str
    type: ProcedureType
    price: MoneyOut
    estimated_cost: MoneyOut
    return_interval_days: int | None
    default_modality: Modality
    split_override: MoneyOut | None = None
    is_active: bool
    is_invasive: bool
    session_plan: SessionPlan
    created_at: datetime
    updated_at: datetime


class ProcedureListOut(OutputSchema):
    items: list[ProcedureOut]
    total_count: int
    page: int
    page_size: int


class ProcedureTemplateOut(OutputSchema):
    template_id: str
    name: str
    type: str = "SERVICE"
    suggested_price: MoneyOut
    suggested_cost: MoneyOut
    suggested_return_interval_days: int | None
    category: str
    is_suggested: bool = True


class ProcedureFromTemplateCreate(InputSchema):
    template_id: str = Field(description="Identificador do template (slug)")
    name: str | None = Field(default=None, description="Nome customizado (opcional)")
    price: str | None = Field(default=None, description="Preço customizado (opcional)")
    estimated_cost: str | None = Field(default=None, description="Custo customizado (opcional)")
    return_interval_days: int | None = Field(
        default=None, ge=0, description="Intervalo de retorno customizado (opcional)"
    )
    default_modality: Modality = Modality.IN_PERSON
    split_override: str | None = Field(
        default=None, description="Percentual de comissão customizado (opcional)"
    )
