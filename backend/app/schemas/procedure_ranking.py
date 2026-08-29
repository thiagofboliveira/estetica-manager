from datetime import date
from uuid import UUID

from app.schemas.base import OutputSchema
from app.schemas.types import MoneyOut, RateOut


class ProcedureRankingRowOut(OutputSchema):
    procedure_id: UUID
    procedure_name: str
    gross_revenue: MoneyOut
    net_profit: MoneyOut
    margin: RateOut | None


class ProcedureRankingOut(OutputSchema):
    period: str
    date_from: date
    date_to: date
    rows: list[ProcedureRankingRowOut]
