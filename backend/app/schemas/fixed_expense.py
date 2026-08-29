from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.fixed_expense import ExpensePeriodicity
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class FixedExpenseCreate(InputSchema):
    label: str = Field(min_length=1)
    category: str | None = None
    amount: str = Field(description="Valor decimal do CICLO, ex: '800.00'")
    periodicity: ExpensePeriodicity = ExpensePeriodicity.MONTHLY
    active_from: date = Field(default_factory=date.today)


class FixedExpenseUpdate(InputSchema):
    label: str | None = Field(default=None, min_length=1)
    category: str | None = None
    amount: str | None = None
    periodicity: ExpensePeriodicity | None = None


class FixedExpenseOut(OutputSchema):
    id: UUID
    label: str
    category: str | None
    amount: MoneyOut
    periodicity: ExpensePeriodicity
    active_from: date
    active_to: date | None
    created_at: datetime
    updated_at: datetime
