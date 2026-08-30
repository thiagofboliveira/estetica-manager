import pytest

from app.domain.sales.session_state_machine import (
    SESSION_TRANSITIONS,
    InvalidSessionTransitionError,
    validate_transition,
)
from app.models.session import SessionStatus


def test_todo_status_esta_na_tabela() -> None:
    """Adicionar status ao enum e esquecer da tabela = KeyError em
    produção (backend/ENGENHARIA.md §5)."""
    assert set(SESSION_TRANSITIONS) == set(SessionStatus)


@pytest.mark.parametrize(
    "current,target",
    [
        (SessionStatus.PENDING, SessionStatus.SCHEDULED),
        (SessionStatus.PENDING, SessionStatus.EXPIRED),
        (SessionStatus.SCHEDULED, SessionStatus.CONFIRMED),
        (SessionStatus.SCHEDULED, SessionStatus.COMPLETED),
        (SessionStatus.SCHEDULED, SessionStatus.CANCELLED),
        (SessionStatus.SCHEDULED, SessionStatus.NO_SHOW),
        (SessionStatus.CONFIRMED, SessionStatus.COMPLETED),
        (SessionStatus.CONFIRMED, SessionStatus.CANCELLED),
        (SessionStatus.CONFIRMED, SessionStatus.NO_SHOW),
        (SessionStatus.NO_SHOW, SessionStatus.SCHEDULED),
        (SessionStatus.CANCELLED, SessionStatus.PENDING),
    ],
)
def test_transicoes_validas(current: SessionStatus, target: SessionStatus) -> None:
    validate_transition(current, target)  # não levanta


@pytest.mark.parametrize(
    "current,target",
    [
        (SessionStatus.COMPLETED, SessionStatus.SCHEDULED),
        (SessionStatus.COMPLETED, SessionStatus.PENDING),
        (SessionStatus.EXPIRED, SessionStatus.SCHEDULED),
        (SessionStatus.PENDING, SessionStatus.COMPLETED),
        (SessionStatus.SCHEDULED, SessionStatus.PENDING),
        (SessionStatus.CANCELLED, SessionStatus.COMPLETED),
    ],
)
def test_transicoes_invalidas_levantam(
    current: SessionStatus, target: SessionStatus
) -> None:
    with pytest.raises(InvalidSessionTransitionError):
        validate_transition(current, target)


def test_terminal_nao_tem_saida() -> None:
    assert SESSION_TRANSITIONS[SessionStatus.COMPLETED] == frozenset()
    assert SESSION_TRANSITIONS[SessionStatus.EXPIRED] == frozenset()


def test_transicao_para_mesmo_estado_e_no_op() -> None:
    validate_transition(SessionStatus.SCHEDULED, SessionStatus.SCHEDULED)
