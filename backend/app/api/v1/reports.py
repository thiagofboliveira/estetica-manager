from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ExpensesByCategorySvc, ProcedureRankingSvc
from app.schemas.expenses_by_category import (
    ExpenseByCategoryRowOut,
    ExpensesByCategoryOut,
)
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
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
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

    # Paginação por corte da lista já ordenada (não por LIMIT/OFFSET no
    # banco): o ranking precisa somar TODOS os itens do período antes de
    # ordenar por procedimento — não dá para paginar antes de agregar.
    total_count = len(ranking)
    start = (page - 1) * page_size
    page_rows = ranking[start : start + page_size]

    return ProcedureRankingOut(
        period=resolved.kind.value,
        date_from=resolved.date_from,
        date_to=resolved.date_to,
        total_count=total_count,
        page=page,
        page_size=page_size,
        rows=[
            ProcedureRankingRowOut(
                procedure_id=row.procedure_id,
                procedure_name=row.procedure_name,
                gross_revenue=row.gross_revenue,
                net_profit=row.net_profit,
                margin=row.margin,
                session_count=row.session_count,
            )
            for row in page_rows
        ],
    )


@router.get("/expenses-by-category", response_model=ExpensesByCategoryOut)
def get_expenses_by_category(svc: ExpensesByCategorySvc) -> ExpensesByCategoryOut:
    rows = svc.get_breakdown()
    return ExpensesByCategoryOut(
        rows=[
            ExpenseByCategoryRowOut(category=row.category, monthly_amount=row.monthly_amount)
            for row in rows
        ]
    )
