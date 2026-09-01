from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from hypothesis import given
from hypothesis import strategies as st

from app.domain.financial.attribution import (
    AttributedCandidate,
    calculate_attributed_revenue,
)
from app.models.professional import Professional
from app.services.attribution_service import AttributionService


def test_attribution_happy_path_and_window_filter():
    """Testa atribuição dentro da janela de 21 dias para oportunidade OVERDUE."""
    patient_id = uuid4()
    sale_id_1 = uuid4()
    sale_id_2 = uuid4()

    # Oportunidade 1: Contatada em 2026-08-10, vencida em 2026-07-20 (OVERDUE > 7d).
    # Venda realizada em 2026-08-15 (5 dias após contato -> dentro de 21d). Lucro R$ 300,00.
    c1 = AttributedCandidate(
        opportunity_id=uuid4(),
        patient_id=patient_id,
        due_date=date(2026, 7, 20),
        contacted_at=datetime(2026, 8, 10, 14, 0),
        resolved_by_sale_id=sale_id_1,
        sale_sold_at=datetime(2026, 8, 15, 10, 0),
        sale_net_profit=Decimal("300.00"),
    )

    # Oportunidade 2: Contatada em 2026-08-01, vencida em 2026-07-01.
    # Venda realizada em 2026-08-25 (24 dias após contato -> FORA de 21d).
    c2 = AttributedCandidate(
        opportunity_id=uuid4(),
        patient_id=patient_id,
        due_date=date(2026, 7, 1),
        contacted_at=datetime(2026, 8, 1, 10, 0),
        resolved_by_sale_id=sale_id_2,
        sale_sold_at=datetime(2026, 8, 25, 10, 0),
        sale_net_profit=Decimal("200.00"),
    )

    result = calculate_attributed_revenue([c1, c2], subscription_fee=Decimal("100.00"))

    assert result.attributed_revenue == Decimal("300.00")
    assert result.attributed_sale_count == 1
    assert result.patients_reactivated == 1
    assert result.roi_ratio == Decimal("3.0")


def test_attribution_ignores_upcoming_and_uncontacted():
    """Oportunidades UPCOMING (não vencidas) ou sem registro de contato são ignoradas."""
    patient_id = uuid4()
    sale_id = uuid4()

    # Oportunidade UPCOMING: due_date amanhã (2026-08-11), contato hoje (2026-08-10).
    c_upcoming = AttributedCandidate(
        opportunity_id=uuid4(),
        patient_id=patient_id,
        due_date=date(2026, 8, 11),
        contacted_at=datetime(2026, 8, 10, 10, 0),
        resolved_by_sale_id=sale_id,
        sale_sold_at=datetime(2026, 8, 10, 11, 0),
        sale_net_profit=Decimal("150.00"),
    )

    # Oportunidade sem contato registrado
    c_uncontacted = AttributedCandidate(
        opportunity_id=uuid4(),
        patient_id=patient_id,
        due_date=date(2026, 7, 1),
        contacted_at=None,
        resolved_by_sale_id=sale_id,
        sale_sold_at=datetime(2026, 8, 10, 11, 0),
        sale_net_profit=Decimal("150.00"),
    )

    result = calculate_attributed_revenue([c_upcoming, c_uncontacted])
    assert result.attributed_revenue == Decimal("0.00")
    assert result.attributed_sale_count == 0
    assert result.patients_reactivated == 0
    assert result.roi_ratio == Decimal("0.0")


def test_attribution_deduplicates_same_sale_for_multiple_opportunities():
    """Se uma mesma venda de pacote resolveu 2 oportunidades OVERDUE, não conta lucro duplo."""
    patient_1 = uuid4()
    patient_2 = uuid4()
    single_sale_id = uuid4()

    c1 = AttributedCandidate(
        opportunity_id=uuid4(),
        patient_id=patient_1,
        due_date=date(2026, 7, 1),
        contacted_at=datetime(2026, 8, 10, 10, 0),
        resolved_by_sale_id=single_sale_id,
        sale_sold_at=datetime(2026, 8, 11, 10, 0),
        sale_net_profit=Decimal("500.00"),
    )

    c2 = AttributedCandidate(
        opportunity_id=uuid4(),
        patient_id=patient_2,
        due_date=date(2026, 7, 1),
        contacted_at=datetime(2026, 8, 10, 10, 0),
        resolved_by_sale_id=single_sale_id,
        sale_sold_at=datetime(2026, 8, 11, 10, 0),
        sale_net_profit=Decimal("500.00"),
    )

    result = calculate_attributed_revenue([c1, c2], subscription_fee=Decimal("100.00"))

    assert result.attributed_revenue == Decimal("500.00")
    assert result.attributed_sale_count == 1
    assert result.patients_reactivated == 2
    assert result.roi_ratio == Decimal("5.0")


@given(
    profits=st.lists(
        st.decimals(min_value=Decimal("10.00"), max_value=Decimal("1000.00"), places=2),
        min_size=1,
        max_size=10,
    ),
    days_after_contact=st.lists(
        st.integers(min_value=0, max_value=30), min_size=1, max_size=10
    ),
)
def test_attribution_property_revenue_bounds(profits, days_after_contact):
    """Property test: Receita atribuída é sempre >= 0 e <= soma de todas as vendas."""
    candidates = []
    base_contact = datetime(2026, 8, 1, 10, 0)
    overdue_due_date = date(2026, 7, 1)

    for p, d in zip(profits, days_after_contact, strict=False):
        sale_id = uuid4()
        candidates.append(
            AttributedCandidate(
                opportunity_id=uuid4(),
                patient_id=uuid4(),
                due_date=overdue_due_date,
                contacted_at=base_contact,
                resolved_by_sale_id=sale_id,
                sale_sold_at=base_contact + timedelta(days=d),
                sale_net_profit=p,
            )
        )

    result = calculate_attributed_revenue(candidates, subscription_fee=Decimal("97.00"))

    total_possible = sum(profits, Decimal("0.00"))
    assert result.attributed_revenue >= Decimal("0.00")
    assert result.attributed_revenue <= total_possible


def test_attribution_service_get_roi():
    """Testa o AttributionService e verifica que period.kind.value é retornado corretamente (BUG-BACK-S2-01)."""
    mock_opp_repo = MagicMock()
    mock_opp_repo.list_attributed.return_value = []

    mock_prof_repo = MagicMock()
    mock_prof = Professional(
        id=uuid4(),
        user_id=uuid4(),
        name="Dra. Teste",
        timezone="America/Sao_Paulo",
    )
    mock_prof_repo.get_current.return_value = mock_prof

    svc = AttributionService(
        opportunity_repo=mock_opp_repo,
        professional_repo=mock_prof_repo,
    )

    result, period_name, d_from, d_to, is_estimated = svc.get_roi(filter_name="this_month")

    assert result.attributed_revenue == Decimal("0.00")
    assert result.attributed_sale_count == 0
    assert period_name == "MONTH"
    assert is_estimated is True
    assert d_from <= d_to
