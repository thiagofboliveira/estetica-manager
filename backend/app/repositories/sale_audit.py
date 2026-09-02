from app.models.sale_audit import SaleAudit
from app.repositories.base import TenantRepository


class SaleAuditRepository(TenantRepository[SaleAudit]):
    model = SaleAudit
