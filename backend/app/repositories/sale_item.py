from datetime import date
from uuid import UUID

from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem
from app.repositories.base import TenantRepository


class SaleItemRepository(TenantRepository[SaleItem]):
    model = SaleItem

    def list_for_sale(self, sale_id: UUID) -> list[SaleItem]:
        stmt = self._scoped().where(SaleItem.sale_id == sale_id)
        return list(self._session.scalars(stmt))

    def list_with_sale_totals_in_period(
        self, date_from: date, date_to: date
    ) -> list[tuple[SaleItem, Sale]]:
        """Itens de vendas ACTIVE com sold_at no período — junto com a
        Sale pai, para o ranking (TASK-024) precisar de split/fee/gross
        da venda inteira para ratear entre os itens (§13, v7.1)."""
        stmt = (
            self._scoped()
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.ACTIVE)
            .where(Sale.sold_at >= date_from)
            .where(Sale.sold_at <= date_to)
            .add_columns(Sale)
        )
        return [(item, sale) for item, sale in self._session.execute(stmt).all()]
