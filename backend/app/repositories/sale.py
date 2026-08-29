from datetime import date

from sqlalchemy import exists

from app.models.sale import Sale, SaleStatus
from app.repositories.base import TenantRepository


class SaleRepository(TenantRepository[Sale]):
    model = Sale

    def find_by_idempotency_key(self, key: str) -> Sale | None:
        stmt = self._scoped().where(Sale.idempotency_key == key)
        return self._session.scalars(stmt).one_or_none()

    def list_in_period(self, date_from: date, date_to: date) -> list[Sale]:
        """Vendas ACTIVE com sold_at no intervalo [date_from, date_to],
        inclusive nos dois extremos (T-022/T-023). REFUNDED não entra
        no dashboard — reversão total (MVP v6 §11.4)."""
        stmt = (
            self._scoped()
            .where(Sale.status == SaleStatus.ACTIVE)
            .where(Sale.sold_at >= date_from)
            .where(Sale.sold_at <= date_to)
        )
        return list(self._session.scalars(stmt))

    def has_any_sale(self) -> bool:
        """T-022a, contrato C-2: existe ALGUMA venda no histórico do
        tenant, independente do período filtrado — distingue "nunca
        vendeu nada" (first-run) de "não vendeu neste mês"."""
        stmt = exists(self._scoped().where(Sale.status == SaleStatus.ACTIVE)).select()
        return bool(self._session.scalar(stmt))
