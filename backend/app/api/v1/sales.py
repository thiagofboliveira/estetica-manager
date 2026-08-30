from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response, status

from app.api.deps import SaleSvc
from app.models.sale_item import SaleItem
from app.models.session import Session as SessionModel
from app.schemas.sale import SaleCreate, SaleItemOut, SaleOut, SessionOut
from app.services.sale_service import (
    IdempotencyKeyConflictError,
    PatientNotFoundForSaleError,
    ProcedureNotFoundForSaleError,
    SaleNotFoundError,
)

router = APIRouter(prefix="/sales", tags=["sales"])


def _to_sale_out(svc: SaleSvc, sale) -> SaleOut:
    items: list[SaleItem] = svc.get_items(sale.id)
    sessions: list[SessionModel] = svc.get_sessions_for_items([i.id for i in items])
    out = SaleOut.model_validate(sale)
    out.items = [SaleItemOut.model_validate(i) for i in items]
    out.sessions = [SessionOut.model_validate(s) for s in sessions]
    return out


@router.post("", response_model=SaleOut)
def create_sale(
    payload: SaleCreate,
    svc: SaleSvc,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> SaleOut:
    """T-015/T-015a — contrato C-1 de idempotência: mesma Idempotency-Key
    + mesmo corpo em 24h devolve a MESMA venda com 200 (não cria
    duplicata). Chave nova ou corpo diferente com chave repetida segue
    o caminho normal: 201 para venda genuinamente nova, 409 se a MESMA
    chave for reusada com um corpo DIFERENTE (a intenção mudou)."""
    was_existing = bool(
        idempotency_key and svc.find_existing_by_idempotency_key(idempotency_key)
    )
    try:
        sale = svc.create(payload, idempotency_key)
    except PatientNotFoundForSaleError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Paciente não encontrado"
        ) from exc
    except ProcedureNotFoundForSaleError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Procedimento não encontrado"
        ) from exc
    except IdempotencyKeyConflictError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Idempotency-Key já usada com um corpo diferente",
        ) from exc
    response.status_code = (
        status.HTTP_200_OK if was_existing else status.HTTP_201_CREATED
    )
    return _to_sale_out(svc, sale)


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: UUID, svc: SaleSvc) -> SaleOut:
    try:
        sale = svc.get(sale_id)
    except SaleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venda não encontrada") from exc
    return _to_sale_out(svc, sale)


@router.post("/{sale_id}/cancel", response_model=SaleOut)
def cancel_sale(
    sale_id: UUID,
    svc: SaleSvc,
    reason: str | None = None,
) -> SaleOut:
    """Cancela uma venda e todas as suas sessões não concluídas (TASK-017)."""
    try:
        sale = svc.cancel(sale_id, reason)
        return _to_sale_out(svc, sale)
    except SaleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venda não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post("/{sale_id}/refund", response_model=SaleOut)
def refund_sale(
    sale_id: UUID,
    svc: SaleSvc,
    reason: str | None = None,
) -> SaleOut:
    """Estorna uma venda e cancela as sessões pendentes/agendadas (TASK-017)."""
    try:
        sale = svc.refund(sale_id, reason)
        return _to_sale_out(svc, sale)
    except SaleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venda não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
