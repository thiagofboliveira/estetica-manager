from app.models.financial_settings import FinancialSettings
from app.repositories.base import TenantRepository


class FinancialSettingsRepository(TenantRepository[FinancialSettings]):
    model = FinancialSettings

    def get_singleton(self) -> FinancialSettings | None:
        return self._session.scalars(self._scoped()).one_or_none()
