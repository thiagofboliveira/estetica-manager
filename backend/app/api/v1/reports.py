from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ProcedureRankingSvc
from app.schemas.procedure_ranking import ProcedureRankingOut, ProcedureRankingRowOut

router = APIRouter(prefix="/reports", tags=["reports"])

_VALID_FILTERS = {"today", "last_7_days", "this_month", "last_month", "custom"}


@router.get("/procedures", response_model=ProcedureRankingOut)
def get_procedure_ranking(
    svc: ProcedureRankingSvc,
    period: str = Query(
        default="this_month",
        description="today|last_7_days|this_month|last_month|custom",
    ),
    date_from: date | None = Query(
        default=None, description="Obrigatório se period=custom"
    ),
    date_to: date | None = Query(
        default=None, description="Obrigatório se period=custom"
    ),
) -> ProcedureRankingOut:
    if period not in _VALID_FILTERS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"period inválido: {period!r}. Use um de {sorted(_VALID_FILTERS)}",
        )
    try:
        ranking, resolved = svc.get_ranking(
            filter_name=period, custom_from=date_from, custom_to=date_to
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return ProcedureRankingOut(
        period=resolved.kind.value,
        date_from=resolved.date_from,
        date_to=resolved.date_to,
        rows=[
            ProcedureRankingRowOut(
                procedure_id=row.procedure_id,
                procedure_name=row.procedure_name,
                gross_revenue=row.gross_revenue,
                net_profit=row.net_profit,
                margin=row.margin,
            )
            for row in ranking
        ],
    )
