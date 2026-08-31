from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AttributionSvc, DashboardSvc
from app.schemas.dashboard import DashboardOut, ROIOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_VALID_FILTERS = {"today", "last_7_days", "this_month", "last_month", "custom"}


@router.get("", response_model=DashboardOut)
def get_dashboard(
    svc: DashboardSvc,
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
        no_show_count=result.no_show_count,
        no_show_rate=result.no_show_rate,
    )


@router.get("/roi", response_model=ROIOut)
def get_roi(
    svc: AttributionSvc,
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
) -> ROIOut:
    """Retorna a Receita Mensal Atribuível ao Sistema (RMAS) e ROI (EPIC-S2-01, TASK-BACK-S2-04)."""
    if period not in _VALID_FILTERS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"period inválido: {period!r}. Use um de {sorted(_VALID_FILTERS)}",
        )
    try:
        result, period_name, d_from, d_to, is_estimated = svc.get_roi(
            filter_name=period, custom_from=date_from, custom_to=date_to
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    roi_str = f"{result.roi_ratio}x" if result.roi_ratio is not None else None

    return ROIOut(
        attributed_revenue=result.attributed_revenue,
        attributed_sale_count=result.attributed_sale_count,
        patients_reactivated=result.patients_reactivated,
        subscription_fee=result.subscription_fee,
        roi_ratio=roi_str,
        period=period_name,
        date_from=d_from,
        date_to=d_to,
        is_estimated=is_estimated,
    )
