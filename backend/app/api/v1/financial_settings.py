from fastapi import APIRouter

from app.api.deps import FinancialSettingsSvc
from app.schemas.financial_settings import FinancialSettingsOut, FinancialSettingsUpdate

router = APIRouter(prefix="/financial-settings", tags=["financial-settings"])


@router.get("", response_model=FinancialSettingsOut)
def get_financial_settings(svc: FinancialSettingsSvc) -> FinancialSettingsOut:
    return FinancialSettingsOut.model_validate(svc.get_or_create_default())


@router.patch("", response_model=FinancialSettingsOut)
def update_financial_settings(
    payload: FinancialSettingsUpdate, svc: FinancialSettingsSvc
) -> FinancialSettingsOut:
    return FinancialSettingsOut.model_validate(svc.update(payload))
