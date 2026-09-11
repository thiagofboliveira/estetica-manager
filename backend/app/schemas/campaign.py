from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CampaignTemplateBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Título descritivo do modelo de campanha")
    category: str = Field(default="promos", max_length=50, description="Categoria: promos, retencao, reativacao, aniversario, outros")
    description: str | None = Field(default=None, max_length=1000, description="Explicação breve do objetivo da mensagem")
    message_text: str = Field(..., min_length=3, max_length=5000, description="Texto da mensagem com placeholders {nome}, {clinica}")


class CampaignTemplateCreate(CampaignTemplateBase):
    pass


class CampaignTemplateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    message_text: str | None = Field(default=None, min_length=3, max_length=5000)
    is_active: bool | None = None


class CampaignTemplateOut(CampaignTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    professional_id: UUID | None = None
    clinic_id: UUID | None = None
    is_system: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
