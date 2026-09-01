from decimal import Decimal

from app.core.money import money
from app.domain.financial.calculator import (
    FeePayer,
    FeeRule,
    LineItem,
    PaymentMethod,
    SaleParams,
    SplitBase,
    calculate_sale,
)


def test_split_override_single_item():
    """Quando o procedimento tem split_override (ex: 40%), ele sobrepõe os 30% da clínica."""
    item = LineItem(
        unit_price=Decimal("1000.00"),
        quantity=1,
        unit_cost_estimated=Decimal("300.00"),
        session_costs=[Decimal("300.00")],
        split_override=Decimal("40.00"),  # 40% em vez de 30%
    )
    params = SaleParams(
        split_clinic_percentage=Decimal("30.00"),
        split_base=SplitBase.GROSS,
        fee_payer=FeePayer.PROFESSIONAL,
        payment_method=PaymentMethod.PIX,
        installments=1,
        discount_amount=Decimal("0.00"),
        fee_rules=[],
    )

    result = calculate_sale([item], params)

    assert result.gross_amount == Decimal("1000.00")
    # Split de 40% sobre 1000 = 400
    assert result.split_amount == Decimal("400.00")
    # Lucro: 1000 - 400 (split) - 0 (taxa) - 300 (custo) = 300
    assert result.net_profit == Decimal("300.00")


def test_split_override_multiple_items_with_mixed_splits():
    """Venda com 2 itens: Item 1 com split_override de 20%, Item 2 sem override (usa 30% default)."""
    item1 = LineItem(
        unit_price=Decimal("200.00"),
        quantity=1,
        unit_cost_estimated=Decimal("50.00"),
        session_costs=[Decimal("50.00")],
        split_override=Decimal("20.00"),
    )
    item2 = LineItem(
        unit_price=Decimal("500.00"),
        quantity=1,
        unit_cost_estimated=Decimal("100.00"),
        session_costs=[Decimal("100.00")],
        split_override=None,  # usa default 30%
    )
    params = SaleParams(
        split_clinic_percentage=Decimal("30.00"),
        split_base=SplitBase.GROSS,
        fee_payer=FeePayer.PROFESSIONAL,
        payment_method=PaymentMethod.PIX,
        installments=1,
        discount_amount=Decimal("0.00"),
        fee_rules=[],
    )

    result = calculate_sale([item1, item2], params)

    # Item 1: 200 * 20% = 40
    # Item 2: 500 * 30% = 150
    # Total Split: 40 + 150 = 190
    assert result.gross_amount == Decimal("700.00")
    assert result.split_amount == Decimal("190.00")
    # Lucro: 700 - 190 (split) - 150 (custos) = 360
    assert result.net_profit == Decimal("360.00")


def test_split_override_with_discount_and_net_of_fee():
    """Split override aplicado sobre base líquida de desconto e de taxa (NET_OF_FEE)."""
    item1 = LineItem(
        unit_price=Decimal("400.00"),
        quantity=1,
        unit_cost_estimated=Decimal("50.00"),
        session_costs=[Decimal("50.00")],
        split_override=Decimal("25.00"),
    )
    item2 = LineItem(
        unit_price=Decimal("600.00"),
        quantity=1,
        unit_cost_estimated=Decimal("100.00"),
        session_costs=[Decimal("100.00")],
        split_override=Decimal("50.00"),
    )
    # Desconto total de 100 -> Item 1 (40% do total) fica com 40 de desc -> Net = 360
    # Item 2 (60% do total) fica com 60 de desc -> Net = 540
    # Bruto = 900
    # Taxa 10% = 90 -> Item 1 taxa = 36 -> Base Item 1 = 324
    # Item 2 taxa = 54 -> Base Item 2 = 486
    # Split Item 1 (25% de 324) = 81.00
    # Split Item 2 (50% de 486) = 243.00
    # Total Split = 324.00
    params = SaleParams(
        split_clinic_percentage=Decimal("30.00"),
        split_base=SplitBase.NET_OF_FEE,
        fee_payer=FeePayer.PROFESSIONAL,
        payment_method=PaymentMethod.CREDIT,
        installments=1,
        discount_amount=Decimal("100.00"),
        fee_rules=[
            FeeRule(
                installments_min=1,
                installments_max=1,
                fee_percentage=Decimal("10.00"),
            )
        ],
    )

    result = calculate_sale([item1, item2], params)

    assert result.gross_amount == Decimal("900.00")
    assert result.fee_amount == Decimal("90.00")
    assert result.split_amount == Decimal("324.00")
    # Lucro: 900 - 324 (split) - 90 (taxa) - 150 (custo) = 336.00
    assert result.net_profit == money(Decimal("336.00"))
