from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import (
    AttributionSvc,
    CurrentUser,
    DashboardSvc,
    DbSession,
    EventSvc,
    resolve_clinic_scope,
)
from app.domain.events import EventName
from app.schemas.dashboard import (
    DashboardOut,
    MonthlyReceivableOut,
    ReceivablesOut,
    ROIOut,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_VALID_FILTERS = {"today", "last_7_days", "this_month", "last_month", "custom"}


@router.get("", response_model=DashboardOut)
def get_dashboard(
    svc: DashboardSvc,
    events: EventSvc,
    user: CurrentUser,
    session: DbSession,
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
    scope: str = Query(default="me", description="me | clinic"),
    professional_id: UUID | None = Query(default=None),
) -> DashboardOut:
    if period not in _VALID_FILTERS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"period inválido: {period!r}. Use um de {sorted(_VALID_FILTERS)}",
        )

    target_pids, resolved_scope, prof_count = resolve_clinic_scope(
        user=user,
        session=session,
        scope=scope,
        target_professional_id=professional_id,
    )

    try:
        if resolved_scope == "me" and target_pids == [user.id]:
            result, resolved = svc.get_dashboard(
                filter_name=period, custom_from=date_from, custom_to=date_to
            )
        else:
            result, resolved = svc.get_aggregated_dashboard(
                professional_ids=target_pids,
                filter_name=period,
                custom_from=date_from,
                custom_to=date_to,
            )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    if result.has_any_data:
        events.track_first(EventName.FIRST_PROFIT_VIEWED)

    public_booking_count = events.count_by_name(EventName.PUBLIC_BOOKING_CREATED.value)

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
        breakeven_remaining_amount=result.breakeven_remaining_amount,
        breakeven_remaining_sessions_estimate=result.breakeven_remaining_sessions_estimate,
        breakeven_alert=result.breakeven_alert,
        public_booking_count=public_booking_count,
        scope=resolved_scope,
        professionals_count=prof_count,
    )


@router.get("/roi", response_model=ROIOut)
def get_roi(
    svc: AttributionSvc,
    events: EventSvc,
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
    events.track_first(EventName.FIRST_PROFIT_VIEWED)

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
        no_show_avoided_count=result.no_show_avoided_count,
        no_show_avoided_revenue=result.no_show_avoided_revenue,
    )


@router.get("/receivables", response_model=ReceivablesOut)
def get_receivables(
    svc: DashboardSvc,
    user: CurrentUser,
    session: DbSession,
    months_ahead: int = Query(default=12, ge=1, le=24),
    scope: str = Query(default="me", description="me | clinic"),
    professional_id: UUID | None = Query(default=None),
) -> ReceivablesOut:
    """Retorna projeção de fluxo de caixa futuro de recebíveis de cartão de crédito parcelado (EPIC-S3-03)."""
    target_pids, resolved_scope, _ = resolve_clinic_scope(
        user=user,
        session=session,
        scope=scope,
        target_professional_id=professional_id,
    )
    if resolved_scope == "me" and target_pids == [user.id]:
        projection = svc.get_receivables_projection(months_ahead=months_ahead)
    else:
        # Aggregated projection over the target professionals
        from app.db.session import tenant_session
        from app.domain.financial.receivables import (
            SaleReceivableInput,
            project_monthly_receivables,
        )
        from app.repositories.professional import ProfessionalRepository
        from app.repositories.sale import SaleRepository

        prof = ProfessionalRepository(session, user.id).get_current()
        from app.core.tz import today_in_timezone
        today = today_in_timezone(prof.timezone)

        all_sales_inputs: list[SaleReceivableInput] = []
        for pid in target_pids:
            with tenant_session(pid) as sess:
                s_repo = SaleRepository(sess, pid)
                for s in s_repo.list(limit=5000):
                    if s.status.value == "ACTIVE":
                        all_sales_inputs.append(
                            SaleReceivableInput(
                                sale_id=str(s.id),
                                sold_at=s.sold_at,
                                payment_method=s.payment_method.value
                                if hasattr(s.payment_method, "value")
                                else str(s.payment_method),
                                installments=s.installments,
                                net_received_amount=s.gross_amount - s.fee_amount_applied,
                                is_anticipated=bool(
                                    (s.snapshot_payload or {}).get("anticipates_all", False)
                                ),
                            )
                        )
        projection = project_monthly_receivables(
            sales=all_sales_inputs,
            reference_date=today,
            months_ahead=months_ahead,
        )

    total = sum((p.total_amount for p in projection), Decimal("0.00"))

    return ReceivablesOut(
        total_projected_amount=total,
        months=[
            MonthlyReceivableOut(
                year_month=p.year_month,
                total_amount=p.total_amount,
                installment_count=p.installment_count,
            )
            for p in projection
        ],
    )
