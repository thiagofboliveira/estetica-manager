"""Rotas de Campanhas e Modelos de Mensagens (WhatsApp)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CampaignSvc, CurrentUser
from app.schemas.campaign import (
    CampaignTemplateCreate,
    CampaignTemplateOut,
    CampaignTemplateUpdate,
)
from app.services.campaign_service import CampaignTemplateNotFoundError

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/templates", response_model=list[CampaignTemplateOut])
def list_campaign_templates(
    svc: CampaignSvc,
    category: str | None = Query(
        default=None,
        description="Filtro opcional por categoria (promos, retencao, reativacao, aniversario, outros)",
    ),
) -> list[CampaignTemplateOut]:
    """Retorna os modelos de campanha (padronizados + customizados da clínica)."""
    return svc.list_templates(category=category)


@router.post("/templates", response_model=CampaignTemplateOut, status_code=status.HTTP_201_CREATED)
def create_campaign_template(
    payload: CampaignTemplateCreate,
    svc: CampaignSvc,
    current_user: CurrentUser,
) -> CampaignTemplateOut:
    """Cria um novo modelo de campanha customizado para a clínica."""
    return svc.create_template(payload, clinic_id=current_user.clinic_id)


@router.put("/templates/{template_id}", response_model=CampaignTemplateOut)
def update_campaign_template(
    template_id: UUID,
    payload: CampaignTemplateUpdate,
    svc: CampaignSvc,
) -> CampaignTemplateOut:
    """Atualiza um modelo de campanha existente."""
    try:
        return svc.update_template(template_id, payload)
    except CampaignTemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de campanha não encontrado",
        ) from None


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign_template(
    template_id: UUID,
    svc: CampaignSvc,
) -> None:
    """Remove um modelo customizado de campanha."""
    try:
        svc.delete_template(template_id)
    except CampaignTemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de campanha não encontrado",
        ) from None
