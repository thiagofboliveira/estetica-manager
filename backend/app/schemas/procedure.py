from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.models.procedure import ProcedureType
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class ProcedureCreate(InputSchema):
    name: str = Field(min_length=1)
    type: ProcedureType = ProcedureType.SERVICE
    price: str = Field(description="Valor decimal, ex: '150.00'")
    estimated_cost: str = Field(description="Valor decimal, ex: '40.00'")
    return_interval_days: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _produto_sem_intervalo_de_retorno(self) -> "ProcedureCreate":
        # Produto revendido não tem janela de retorno clínico (MVP v6 §9).
        if self.type is ProcedureType.PRODUCT:
            self.return_interval_days = None
        return self


class ProcedureUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=1)
    price: str | None = None
    estimated_cost: str | None = None
    return_interval_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProcedureOut(OutputSchema):
    id: UUID
    name: str
    type: ProcedureType
    price: MoneyOut
    estimated_cost: MoneyOut
    return_interval_days: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
