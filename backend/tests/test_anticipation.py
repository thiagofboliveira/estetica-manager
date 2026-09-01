from datetime import date, timedelta
from decimal import Decimal

from app.domain.financial.calculator import (
    FeePayer,
    FeeRule,
    LineItem,
    PaymentMethod,
    SaleParams,
    SplitBase,
    calculate_sale,
    expected_receipt_date,
)


def test_anticipation_adds_extra_fee():
    """Quando antecipação está ativa, taxa de antecipação por parcela é somada à taxa da maquininha."""
    item = LineItem(
        unit_price=Decimal("1200.00"),
        quantity=1,
        unit_cost_estimated=Decimal("200.00"),
        session_costs=[Decimal("200.00")],
    )
    # 3x no crédito. Taxa base: 3.00%. Taxa antecipação: 1.50% por parcela -> 3 * 1.50 = 4.50%
    # Taxa total efetiva = 3.00 + 4.50 = 7.50%
    # 7.50% sobre 1200 = 90.00
    params = SaleParams(
        split_clinic_percentage=Decimal("0.00"),
        split_base=SplitBase.GROSS,
        fee_payer=FeePayer.PROFESSIONAL,
        payment_method=PaymentMethod.CREDIT,
        installments=3,
        discount_amount=Decimal("0.00"),
        fee_rules=[
            FeeRule(
                installments_min=1,
                installments_max=6,
                fee_percentage=Decimal("3.00"),
            )
        ],
        anticipates_all=True,
        anticipation_rate_per_installment=Decimal("1.50"),
    )

    result = calculate_sale([item], params)

    assert result.fee_rate == Decimal("7.50")
    assert result.fee_amount == Decimal("90.00")
    # Lucro: 1200 - 0 (split) - 90 (taxa com antecipação) - 200 (custo) = 910.00
    assert result.net_profit == Decimal("910.00")


def test_expected_receipt_date_with_anticipation():
    """Crédito parcelado com antecipação cai em D+2 em vez de D+(30*N)."""
    sold_at = date(2026, 8, 1)

    # Sem antecipação: 3 parcelas -> D+90
    receipt_normal = expected_receipt_date(
        PaymentMethod.CREDIT,
        sold_at,
        installments=3,
        anticipates=False,
    )
    assert receipt_normal == sold_at + timedelta(days=90)

    # Com antecipação: D+2
    receipt_anticipado = expected_receipt_date(
        PaymentMethod.CREDIT,
        sold_at,
        installments=3,
        anticipates=True,
    )
    assert receipt_anticipado == sold_at + timedelta(days=2)
