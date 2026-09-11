from app.models.campaign import CampaignTemplate
from app.repositories.base import TenantRepository


class CampaignTemplateRepository(TenantRepository[CampaignTemplate]):
    model = CampaignTemplate

    def list_templates(self, category: str | None = None) -> list[CampaignTemplate]:
        stmt = self._scoped().where(CampaignTemplate.is_active.is_(True))
        if category and category != "all":
            stmt = stmt.where(CampaignTemplate.category == category)
        stmt = stmt.order_by(CampaignTemplate.created_at.desc())
        return list(self._session.scalars(stmt))
