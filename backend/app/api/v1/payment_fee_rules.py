from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import PaymentFeeRuleSvc
from app.schemas.payment_fee_rule import (
    PaymentFeeRuleCreate,
    PaymentFeeRuleOut,
    PaymentFeeRuleUpdate,
)
from app.services.payment_fee_rule_service import PaymentFeeRuleNotFoundError

router = APIRouter(prefix="/payment-fee-rules", tags=["payment-fee-rules"])


@router.get("", response_model=list[PaymentFeeRuleOut])
def list_payment_fee_rules(svc: PaymentFeeRuleSvc) -> list[PaymentFeeRuleOut]:
    return [PaymentFeeRuleOut.model_validate(r) for r in svc.list_or_seed_defaults()]


@router.post("", response_model=PaymentFeeRuleOut, status_code=status.HTTP_201_CREATED)
def create_payment_fee_rule(
    payload: PaymentFeeRuleCreate, svc: PaymentFeeRuleSvc
) -> PaymentFeeRuleOut:
    try:
        return PaymentFeeRuleOut.model_validate(svc.create(payload))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.patch("/{rule_id}", response_model=PaymentFeeRuleOut)
def update_payment_fee_rule(
    rule_id: UUID, payload: PaymentFeeRuleUpdate, svc: PaymentFeeRuleSvc
) -> PaymentFeeRuleOut:
    try:
        rule = svc.update(rule_id, payload)
    except PaymentFeeRuleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regra não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return PaymentFeeRuleOut.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_fee_rule(rule_id: UUID, svc: PaymentFeeRuleSvc) -> None:
    try:
        svc.delete(rule_id)
    except PaymentFeeRuleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regra não encontrada") from exc
