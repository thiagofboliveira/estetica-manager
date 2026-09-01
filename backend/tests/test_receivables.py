from datetime import date
from decimal import Decimal

from app.domain.financial.receivables import (
    SaleReceivableInput,
    project_monthly_receivables,
)


def test_receivables_projection_single_and_installments():
    """Testa projeção de parcelas futuras distribuídas ao longo dos meses."""
    ref_date = date(2026, 8, 1)

    # Venda 1: Pix de R$ 200 em agosto -> cai em agosto
    s1 = SaleReceivableInput(
        sale_id="1",
        sold_at=date(2026, 8, 5),
        payment_method="PIX",
        installments=1,
        net_received_amount=Decimal("200.00"),
    )

    # Venda 2: Cartão 3x de R$ 300 (total 900) em 10 de agosto
    # Parcela 1 (+30d = 09/Set): ~R$ 300,00
    # Parcela 2 (+60d = 09/Out): ~R$ 300,00
    # Parcela 3 (+90d = 08/Nov): ~R$ 300,00
    s2 = SaleReceivableInput(
        sale_id="2",
        sold_at=date(2026, 8, 10),
        payment_method="CREDIT",
        installments=3,
        net_received_amount=Decimal("900.00"),
        is_anticipated=False,
    )

    # Venda 3: Cartão 2x de R$ 500 antecipado -> cai em agosto
    s3 = SaleReceivableInput(
        sale_id="3",
        sold_at=date(2026, 8, 15),
        payment_method="CREDIT",
        installments=2,
        net_received_amount=Decimal("450.00"),
        is_anticipated=True,
    )

    projection = project_monthly_receivables([s1, s2, s3], reference_date=ref_date, months_ahead=6)

    # 6 meses projetados: 2026-08, 2026-09, 2026-10, 2026-11, 2026-12, 2027-01
    assert len(projection) == 6
    assert projection[0].year_month == "2026-08"
    assert projection[0].total_amount == Decimal("650.00")  # 200 (pix) + 450 (antecipado)

    assert projection[1].year_month == "2026-09"
    assert projection[1].total_amount == Decimal("300.00")

    assert projection[2].year_month == "2026-10"
    assert projection[2].total_amount == Decimal("300.00")

    assert projection[3].year_month == "2026-11"
    assert projection[3].total_amount == Decimal("300.00")

    assert projection[4].year_month == "2026-12"
    assert projection[4].total_amount == Decimal("0.00")
