"""Máquina de estados de ReturnOpportunity (MVP v7.1 §14, TASK-025).

PURO: sem SQLAlchemy, sem FastAPI, sem app.models (mesma disciplina de
app.domain.sales.session_state_machine — ver
tests/test_architecture.py::test_dominio_nao_importa_infraestrutura).

Eixo de STATUS (persistido, movido por evento) — distinto do eixo de
TIMING (UPCOMING/DUE/OVERDUE, derivado de due_date vs hoje, nunca
persistido — ver app.domain.retention.window):

    OPEN --> CONTACTED
    OPEN --> DISMISSED
    OPEN --> CLOSED : fechamento automático na venda (T-028)
    CONTACTED --> BOOKED
    CONTACTED --> DECLINED
    CONTACTED --> NO_RESPONSE
    CONTACTED --> CLOSED : fechamento automático na venda (T-028)
    NO_RESPONSE --> CONTACTED : nova tentativa
    NO_RESPONSE --> CLOSED : fechamento automático na venda (T-028)
    BOOKED --> CLOSED
    DECLINED --> CLOSED
    DISMISSED --> [*]
    CLOSED --> [*]
"""

from enum import StrEnum
from types import MappingProxyType


class ReturnOpportunityStatus(StrEnum):
    OPEN = "OPEN"
    CONTACTED = "CONTACTED"
    BOOKED = "BOOKED"
    DECLINED = "DECLINED"
    NO_RESPONSE = "NO_RESPONSE"
    DISMISSED = "DISMISSED"
    CLOSED = "CLOSED"


RETURN_OPPORTUNITY_TRANSITIONS: MappingProxyType[
    ReturnOpportunityStatus, frozenset[ReturnOpportunityStatus]
] = MappingProxyType(
    {
        ReturnOpportunityStatus.OPEN: frozenset(
            {
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.DISMISSED,
                ReturnOpportunityStatus.CLOSED,  # fechamento automático na venda (T-028)
            }
        ),
        ReturnOpportunityStatus.CONTACTED: frozenset(
            {
                ReturnOpportunityStatus.BOOKED,
                ReturnOpportunityStatus.DECLINED,
                ReturnOpportunityStatus.NO_RESPONSE,
                ReturnOpportunityStatus.CLOSED,  # fechamento automático na venda (T-028)
            }
        ),
        ReturnOpportunityStatus.NO_RESPONSE: frozenset(
            {
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.CLOSED,  # fechamento automático na venda (T-028)
            }
        ),
        ReturnOpportunityStatus.BOOKED: frozenset({ReturnOpportunityStatus.CLOSED}),
        ReturnOpportunityStatus.DECLINED: frozenset({ReturnOpportunityStatus.CLOSED}),
        ReturnOpportunityStatus.DISMISSED: frozenset(),  # terminal
        ReturnOpportunityStatus.CLOSED: frozenset(),  # terminal
    }
)


class InvalidReturnOpportunityTransitionError(Exception):
    def __init__(
        self, current: ReturnOpportunityStatus, target: ReturnOpportunityStatus
    ) -> None:
        self.current = current
        self.target = target
        super().__init__(f"transição inválida: {current} -> {target}")


def validate_transition(
    current: ReturnOpportunityStatus, target: ReturnOpportunityStatus
) -> None:
    """Levanta InvalidReturnOpportunityTransitionError se a transição não
    é permitida. Chamado pelo service antes de qualquer UPDATE — nunca
    confie que o chamador já validou."""
    if target == current:
        return
    allowed = RETURN_OPPORTUNITY_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidReturnOpportunityTransitionError(current, target)
