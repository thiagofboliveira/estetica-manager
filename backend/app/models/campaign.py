"""CampaignTemplate: Modelagem de modelos de campanhas e disparos WhatsApp.

Invariantes:
- I1: RLS por professional_id (TenantModel)
- I2: isolamento estrito de tenant
- I4: auditoria com timestamps automáticos
"""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel

__all__ = ["CampaignTemplate"]


class CampaignTemplate(TenantModel):
    __tablename__ = "campaign_templates"

    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="promos")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
