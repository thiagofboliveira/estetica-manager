from app.schemas.base import OutputSchema
from app.schemas.types import MoneyOut


class ExpenseByCategoryRowOut(OutputSchema):
    category: str
    monthly_amount: MoneyOut


class ExpensesByCategoryOut(OutputSchema):
    rows: list[ExpenseByCategoryRowOut]
