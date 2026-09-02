from uuid import UUID

from app.models.sale_audit import SaleAudit
from app.repositories.base import TenantRepository


class SaleAuditRepository(TenantRepository[SaleAudit]):
    model = SaleAudit

    def list_for_original_sale(self, original_sale_id: UUID) -> list[SaleAudit]:
        stmt = (
            self._scoped()
            .where(SaleAudit.original_sale_id == original_sale_id)
            .order_by(SaleAudit.corrected_at)
        )
        return list(self._session.scalars(stmt))
