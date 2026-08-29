from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DashboardSvc
from app.schemas.dashboard import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_VALID_FILTERS = {"today", "last_7_days", "this_month", "last_month", "custom"}


@router.get("", response_model=DashboardOut)
def get_dashboard(
    svc: DashboardSvc,
    period: str = Query(default="this_month", description="today|last_7_days|this_month|last_month|custom"),
    date_from: date | None = Query(default=None, description="Obrigatório se period=custom"),
    date_to: date | None = Query(default=None, description="Obrigatório se period=custom"),
) -> DashboardOut:
    if period not in _VALID_FILTERS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"period inválido: {period!r}. Use um de {sorted(_VALID_FILTERS)}",
        )
    try:
        result, resolved = svc.get_dashboard(
            filter_name=period, custom_from=date_from, custom_to=date_to
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return DashboardOut(
        period=resolved.kind.value,
        date_from=resolved.date_from,
        date_to=resolved.date_to,
        has_any_data=result.has_any_data,
        gross_revenue=result.gross_revenue,
        net_profit=result.net_profit,
        fixed_expenses_total=result.fixed_expenses_total,
        net_profit_after_fixed_expenses=result.net_profit_after_fixed_expenses,
        receivable_amount=result.receivable_amount,
        average_margin=result.average_margin,
        sale_count=result.sale_count,
        session_count=result.session_count,
        average_ticket=result.average_ticket,
    )
