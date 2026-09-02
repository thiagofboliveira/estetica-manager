import pytest

from app.domain.retention.return_opportunity_state_machine import (
    RETURN_OPPORTUNITY_TRANSITIONS,
    InvalidReturnOpportunityTransitionError,
    ReturnOpportunityStatus,
    validate_transition,
)


def test_todo_status_esta_na_tabela():
    assert set(RETURN_OPPORTUNITY_TRANSITIONS) == set(ReturnOpportunityStatus)


@pytest.mark.parametrize(
    "current,target",
    [
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.CONTACTED),
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.DISMISSED),
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.CLOSED),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.BOOKED),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.DECLINED),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.NO_RESPONSE),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.CLOSED),
        (ReturnOpportunityStatus.NO_RESPONSE, ReturnOpportunityStatus.CONTACTED),
        (ReturnOpportunityStatus.NO_RESPONSE, ReturnOpportunityStatus.CLOSED),
        (ReturnOpportunityStatus.BOOKED, ReturnOpportunityStatus.CLOSED),
        (ReturnOpportunityStatus.DECLINED, ReturnOpportunityStatus.CLOSED),
    ],
)
def test_transicoes_validas_nao_levantam(current, target):
    validate_transition(current, target)  # não deve levantar


@pytest.mark.parametrize(
    "current,target",
    [
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.BOOKED),
        (ReturnOpportunityStatus.CLOSED, ReturnOpportunityStatus.OPEN),
        (ReturnOpportunityStatus.DISMISSED, ReturnOpportunityStatus.OPEN),
        (ReturnOpportunityStatus.BOOKED, ReturnOpportunityStatus.CONTACTED),
    ],
)
def test_transicoes_invalidas_levantam(current, target):
    with pytest.raises(InvalidReturnOpportunityTransitionError):
        validate_transition(current, target)


def test_transicao_para_o_mesmo_status_e_no_op():
    validate_transition(ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.OPEN)
