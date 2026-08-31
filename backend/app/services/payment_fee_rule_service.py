"""PaymentFeeRuleService — CRUD simples + seed de defaults de mercado
(TASK-008/008a).

Faixas de mercado BR (MVP v6 §8.1): à vista ~3,2%, 2-6x ~9-11%, 7-12x
~13-16%. Populado no primeiro acesso, uma vez — NUNCA copiado de outra
conta.
"""

from decimal import Decimal
from uuid import UUID

from app.core.money import money
from app.models.financial_settings import PaymentMethod
from app.models.payment_fee_rule import PaymentFeeRule
from app.repositories.payment_fee_rule import PaymentFeeRuleRepository
from app.schemas.payment_fee_rule import PaymentFeeRuleCreate, PaymentFeeRuleUpdate

_MARKET_DEFAULTS: list[tuple[PaymentMethod, int, int, str, str]] = [
    (PaymentMethod.PIX, 1, 1, "0.00", "0.00"),
    (PaymentMethod.DEBIT, 1, 1, "1.99", "0.00"),
    (PaymentMethod.CREDIT, 1, 1, "3.20", "0.00"),
    (PaymentMethod.CREDIT, 2, 6, "9.50", "0.00"),
    (PaymentMethod.CREDIT, 7, 12, "13.50", "0.00"),
    (PaymentMethod.CASH, 1, 1, "0.00", "0.00"),
    (PaymentMethod.TRANSFER, 1, 1, "0.00", "0.00"),
]


class PaymentFeeRuleNotFoundError(Exception):
    pass


class PaymentFeeRuleService:
    def __init__(self, repo: PaymentFeeRuleRepository) -> None:
        self._repo = repo

    def _validate_no_overlap(
        self,
        payment_method: PaymentMethod,
        imin: int,
        imax: int,
        exclude_rule_id: UUID | None = None,
    ) -> None:
        existing_rules = self._repo.list_all()
        for r in existing_rules:
            if exclude_rule_id and r.id == exclude_rule_id:
                continue
            if (
                r.payment_method == payment_method
                and max(imin, r.installments_min) <= min(imax, r.installments_max)
            ):
                raise ValueError(
                    f"A faixa de parcelas ({imin} a {imax}) se sobrepõe com a regra existente ({r.installments_min} a {r.installments_max}) para {payment_method.value}."
                )

    def list_or_seed_defaults(self) -> list[PaymentFeeRule]:
        existing = self._repo.list_all()
        if existing:
            return existing

        for method, imin, imax, fee_pct, fixed in _MARKET_DEFAULTS:
            rule = PaymentFeeRule(
                payment_method=method,
                installments_min=imin,
                installments_max=imax,
                fee_percentage=money(Decimal(fee_pct)),
                fixed_fee=money(Decimal(fixed)),
            )
            self._repo.add(rule)
        return self._repo.list_all()

    def create(self, dto: PaymentFeeRuleCreate) -> PaymentFeeRule:
        self._validate_no_overlap(
            dto.payment_method, dto.installments_min, dto.installments_max
        )
        rule = PaymentFeeRule(
            payment_method=dto.payment_method,
            installments_min=dto.installments_min,
            installments_max=dto.installments_max,
            fee_percentage=money(dto.fee_percentage),
            fixed_fee=money(dto.fixed_fee),
        )
        return self._repo.add(rule)

    def get(self, rule_id: UUID) -> PaymentFeeRule:
        rule = self._repo.get(rule_id)
        if rule is None:
            raise PaymentFeeRuleNotFoundError()
        return rule

    def update(self, rule_id: UUID, dto: PaymentFeeRuleUpdate) -> PaymentFeeRule:
        rule = self.get(rule_id)
        data = dto.model_dump(exclude_unset=True)

        new_method = data.get("payment_method", rule.payment_method)
        new_min = data.get("installments_min", rule.installments_min)
        new_max = data.get("installments_max", rule.installments_max)

        self._validate_no_overlap(new_method, new_min, new_max, exclude_rule_id=rule_id)

        if "fee_percentage" in data and data["fee_percentage"] is not None:
            data["fee_percentage"] = money(data["fee_percentage"])
        if "fixed_fee" in data and data["fixed_fee"] is not None:
            data["fixed_fee"] = money(data["fixed_fee"])
        for field, value in data.items():
            setattr(rule, field, value)
        self._repo.flush()
        return rule

    def delete(self, rule_id: UUID) -> None:
        rule = self.get(rule_id)
        self._repo.delete(rule)
        self._repo.flush()
