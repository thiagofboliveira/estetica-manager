from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.financial_settings import FinancialSettings
from app.schemas.financial_settings import FinancialSettingsUpdate
from app.services.financial_settings_service import FinancialSettingsService


def test_update_financial_settings_with_goal():
    mock_repo = MagicMock()
    existing = FinancialSettings(
        split_clinic_percentage=Decimal("0.00"),
        pix_fee_percentage=Decimal("0.00"),
        debit_card_fee_percentage=Decimal("1.99"),
        monthly_revenue_goal=None,
    )
    mock_repo.get_singleton.return_value = existing

    svc = FinancialSettingsService(mock_repo)

    # 1. Definindo meta com string normal
    res = svc.update(FinancialSettingsUpdate(monthly_revenue_goal="15000.00"))
    assert res.monthly_revenue_goal == Decimal("15000.00")
    mock_repo.flush.assert_called()

    # 2. Definindo meta formatada em pt-BR com "R$" e vírgula
    res = svc.update(FinancialSettingsUpdate(monthly_revenue_goal="R$ 25000,50"))
    assert res.monthly_revenue_goal == Decimal("25000.50")

    # 3. Limpando a meta com string vazia
    res = svc.update(FinancialSettingsUpdate(monthly_revenue_goal=""))
    assert res.monthly_revenue_goal is None

    # 4. Limpando a meta com whitespace
    res = svc.update(FinancialSettingsUpdate(monthly_revenue_goal="   "))
    assert res.monthly_revenue_goal is None

    # 5. Limpando a meta com None explícito
    res = svc.update(FinancialSettingsUpdate(monthly_revenue_goal=None))
    assert res.monthly_revenue_goal is None
