from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import FixedExpenseSvc
from app.schemas.fixed_expense import (
    FixedExpenseCreate,
    FixedExpenseOut,
    FixedExpenseUpdate,
)
from app.services.fixed_expense_service import FixedExpenseNotFoundError

router = APIRouter(prefix="/fixed-expenses", tags=["fixed-expenses"])


@router.post("", response_model=FixedExpenseOut, status_code=status.HTTP_201_CREATED)
def create_fixed_expense(payload: FixedExpenseCreate, svc: FixedExpenseSvc) -> FixedExpenseOut:
    return FixedExpenseOut.model_validate(svc.create(payload))


@router.get("", response_model=list[FixedExpenseOut])
def list_fixed_expenses(
    svc: FixedExpenseSvc,
    include_archived: bool = Query(default=False),
) -> list[FixedExpenseOut]:
    expenses = svc.list_all() if include_archived else svc.list_active()
    return [FixedExpenseOut.model_validate(e) for e in expenses]


@router.get("/{expense_id}", response_model=FixedExpenseOut)
def get_fixed_expense(expense_id: UUID, svc: FixedExpenseSvc) -> FixedExpenseOut:
    try:
        expense = svc.get(expense_id)
    except FixedExpenseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada") from exc
    return FixedExpenseOut.model_validate(expense)


@router.patch("/{expense_id}", response_model=FixedExpenseOut)
def update_fixed_expense(
    expense_id: UUID, payload: FixedExpenseUpdate, svc: FixedExpenseSvc
) -> FixedExpenseOut:
    try:
        expense = svc.update(expense_id, payload)
    except FixedExpenseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada") from exc
    return FixedExpenseOut.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_fixed_expense(expense_id: UUID, svc: FixedExpenseSvc) -> None:
    """Fecha active_to=hoje. Nunca hard delete — ver MVP v7.1 §12.5."""
    try:
        svc.archive(expense_id)
    except FixedExpenseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada") from exc
