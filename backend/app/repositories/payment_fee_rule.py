from app.models.financial_settings import PaymentMethod
from app.models.payment_fee_rule import PaymentFeeRule
from app.repositories.base import TenantRepository


class PaymentFeeRuleRepository(TenantRepository[PaymentFeeRule]):
    model = PaymentFeeRule

    def list_all(self) -> list[PaymentFeeRule]:
        stmt = self._scoped().order_by(
            PaymentFeeRule.payment_method, PaymentFeeRule.installments_min
        )
        return list(self._session.scalars(stmt))

    def find_rule(
        self, payment_method: PaymentMethod, installments: int
    ) -> PaymentFeeRule | None:
        for rule in self.list_all():
            if (
                rule.payment_method == payment_method
                and rule.installments_min <= installments <= rule.installments_max
            ):
                return rule
        return None
