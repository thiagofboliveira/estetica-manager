"""FinancialSettingsService — singleton de config por tenant (TASK-007).

Cria com defaults de MERCADO (MVP v6 §8.1) na primeira leitura se ainda
não existir — nunca copiado de outra conta (regra explícita do MVP).
"""

from decimal import Decimal

from app.core.money import money
from app.models.financial_settings import (
    FeePayer,
    FinancialSettings,
    PaymentMethod,
    SplitBase,
)
from app.repositories.financial_settings import FinancialSettingsRepository
from app.schemas.financial_settings import FinancialSettingsUpdate


class FinancialSettingsService:
    def __init__(self, repo: FinancialSettingsRepository) -> None:
        self._repo = repo

    def get_or_create_default(self) -> FinancialSettings:
        settings = self._repo.get_singleton()
        if settings is not None:
            return settings

        # Defaults de mercado (§8.1) — NÃO copiar de outra conta, NÃO
        # usar a config da cliente zero como semente do produto.
        settings = FinancialSettings(
            split_clinic_percentage=Decimal("0.00"),
            split_base=SplitBase.GROSS,
            fee_payer=FeePayer.PROFESSIONAL,
            pix_fee_percentage=Decimal("0.00"),
            debit_card_fee_percentage=Decimal("1.99"),
            default_payment_method=PaymentMethod.PIX,
        )
        return self._repo.add(settings)

    def update(self, dto: FinancialSettingsUpdate) -> FinancialSettings:
        settings = self.get_or_create_default()
        data = dto.model_dump(exclude_unset=True)

        for pct_field in (
            "split_clinic_percentage",
            "pix_fee_percentage",
            "debit_card_fee_percentage",
        ):
            if pct_field in data and data[pct_field] is not None:
                data[pct_field] = money(data[pct_field])

        for field, value in data.items():
            setattr(settings, field, value)

        self._repo.flush()
        return settings
