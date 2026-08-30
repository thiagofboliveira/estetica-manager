from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.retention.enums import ReturnOpportunityStatus, Timing
from app.domain.retention.opportunity_rules import (
    OpportunityItem,
    calculate_due_date,
    calculate_timing,
    group_opportunities_by_patient,
    is_attributed_conversion,
    is_suppressed,
)
from app.domain.retention.state_machine import (
    InvalidReturnOpportunityTransitionError,
    validate_return_transition,
)


def test_calculate_due_date() -> None:
    # 01/03/2026 + 180 dias = 28/08/2026 (TASK-026, MVP v6 §14)
    completed = date(2026, 3, 1)
    due = calculate_due_date(completed, 180)
    assert due == date(2026, 8, 28)


def test_timing_upcoming_due_overdue() -> None:
    hoje = date(2026, 8, 30)

    # > hoje + 7d (ex: 10/09/2026) -> UPCOMING
    assert calculate_timing(date(2026, 9, 10), hoje) == Timing.UPCOMING

    # hoje - 7d <= due <= hoje + 7d (ex: 28/08/2026, 30/08/2026, 05/09/2026) -> DUE
    assert calculate_timing(date(2026, 8, 28), hoje) == Timing.DUE
    assert calculate_timing(date(2026, 8, 30), hoje) == Timing.DUE
    assert calculate_timing(date(2026, 9, 5), hoje) == Timing.DUE

    # < hoje - 7d (ex: 20/08/2026) -> OVERDUE
    assert calculate_timing(date(2026, 8, 20), hoje) == Timing.OVERDUE


def test_is_suppressed_14_days() -> None:
    hoje = date(2026, 8, 30)

    # Nunca contatada -> False
    assert not is_suppressed(None, hoje, suppression_days=14)

    # Contatada há 5 dias -> True
    contato_recente = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)
    assert is_suppressed(contato_recente, hoje, suppression_days=14)

    # Contatada há 15 dias -> False
    contato_antigo = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)
    assert not is_suppressed(contato_antigo, hoje, suppression_days=14)


def test_group_opportunities_by_patient() -> None:
    hoje = date(2026, 8, 30)
    patient_id = uuid4()
    botox_id = uuid4()
    limpeza_id = uuid4()

    opp1 = OpportunityItem(
        id=uuid4(),
        procedure_id=botox_id,
        procedure_name="Botox",
        due_date=date(2026, 8, 27),  # atrasado 3 dias
        timing=Timing.DUE,
        status=ReturnOpportunityStatus.OPEN,
        potential_value=Decimal("1000.00"),
        days_diff=-3,
    )
    opp2 = OpportunityItem(
        id=uuid4(),
        procedure_id=limpeza_id,
        procedure_name="Limpeza de pele",
        due_date=date(2026, 9, 4),  # vence em 5 dias
        timing=Timing.DUE,
        status=ReturnOpportunityStatus.OPEN,
        potential_value=Decimal("250.00"),
        days_diff=5,
    )

    data = [
        (patient_id, "Maria Silva", "11999998888", True, False, None, opp1),
        (patient_id, "Maria Silva", "11999998888", True, False, None, opp2),
    ]

    groups = group_opportunities_by_patient(data, hoje)

    # 1 único card para a Maria
    assert len(groups) == 1
    maria_group = groups[0]
    assert maria_group.patient_name == "Maria Silva"
    assert maria_group.total_potential_value == Decimal("1250.00")
    # Procedimento principal deve ser o mais atrasado (Botox)
    assert maria_group.primary_opportunity.procedure_name == "Botox"
    assert len(maria_group.secondary_opportunities) == 1
    assert maria_group.secondary_opportunities[0].procedure_name == "Limpeza de pele"
    assert maria_group.whatsapp_enabled is True


def test_patient_without_consent_disables_whatsapp() -> None:
    hoje = date(2026, 8, 30)
    patient_id = uuid4()
    opp = OpportunityItem(
        id=uuid4(),
        procedure_id=uuid4(),
        procedure_name="Peeling",
        due_date=date(2026, 8, 30),
        timing=Timing.DUE,
        status=ReturnOpportunityStatus.OPEN,
        potential_value=Decimal("300.00"),
        days_diff=0,
    )

    data = [
        (
            patient_id,
            "Ana",
            "11999997777",
            False,
            False,
            None,
            opp,
        ),  # consent_whatsapp=False
    ]

    groups = group_opportunities_by_patient(data, hoje)
    assert len(groups) == 1
    assert groups[0].whatsapp_enabled is False
    assert "Sem consentimento" in (groups[0].disabled_reason or "")


def test_return_opportunity_state_machine() -> None:
    # Transições válidas
    validate_return_transition(
        ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.CONTACTED
    )
    validate_return_transition(
        ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.BOOKED
    )
    validate_return_transition(
        ReturnOpportunityStatus.BOOKED, ReturnOpportunityStatus.CLOSED
    )
    validate_return_transition(
        ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.DISMISSED
    )

    # Transições proibidas
    with pytest.raises(InvalidReturnOpportunityTransitionError):
        validate_return_transition(
            ReturnOpportunityStatus.CLOSED, ReturnOpportunityStatus.OPEN
        )

    with pytest.raises(InvalidReturnOpportunityTransitionError):
        validate_return_transition(
            ReturnOpportunityStatus.DISMISSED, ReturnOpportunityStatus.CONTACTED
        )


def test_is_attributed_conversion() -> None:
    # T-045b: Janela de atribuição de 21 dias (MVP v6 §15, §19)
    contacted = date(2026, 8, 1)

    # Venda dentro da janela (10 dias depois) -> True
    assert (
        is_attributed_conversion(contacted, date(2026, 8, 11), window_days=21) is True
    )

    # Venda exatamente no limite (21 dias depois) -> True
    assert (
        is_attributed_conversion(contacted, date(2026, 8, 22), window_days=21) is True
    )

    # Venda fora da janela (22 dias depois) -> False
    assert (
        is_attributed_conversion(contacted, date(2026, 8, 23), window_days=21) is False
    )

    # Venda anterior ao contato -> False
    assert (
        is_attributed_conversion(contacted, date(2026, 7, 30), window_days=21) is False
    )

    # Sem contato registrado -> False
    assert is_attributed_conversion(None, date(2026, 8, 11), window_days=21) is False
