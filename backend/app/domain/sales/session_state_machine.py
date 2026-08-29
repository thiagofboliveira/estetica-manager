"""Máquina de estados de Session (MVP v6 §11.4).

PURO: sem SQLAlchemy, sem FastAPI, sem app.models (backend/ENGENHARIA.md
§5/§6 — domain/ não importa infraestrutura, garantido por
tests/test_architecture.py::test_dominio_nao_importa_infraestrutura).
SessionStatus vive AQUI e app.models.session.SessionStatus é só um
re-export dele — a direção permitida é modelo -> domínio, nunca o
contrário.

```
[*] --> PENDING : pacote, sem data
[*] --> SCHEDULED : avulso, com data
PENDING --> SCHEDULED : agendada
SCHEDULED --> CONFIRMED
SCHEDULED --> CANCELLED
SCHEDULED --> NO_SHOW
CONFIRMED --> COMPLETED
CONFIRMED --> CANCELLED
CONFIRMED --> NO_SHOW
NO_SHOW --> SCHEDULED : remarcação
CANCELLED --> PENDING : volta ao saldo do pacote
PENDING --> EXPIRED : validade vencida
COMPLETED --> [*]
EXPIRED --> [*]
```

`SCHEDULED --> COMPLETED` direto (sem passar por CONFIRMED) também é
permitido — confirmação é opcional no fluxo real (nem toda profissional
usa lembrete de confirmação, T-054 é P1).
"""

from enum import StrEnum
from types import MappingProxyType


class SessionStatus(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    EXPIRED = "EXPIRED"


SESSION_TRANSITIONS: MappingProxyType[SessionStatus, frozenset[SessionStatus]] = (
    MappingProxyType(
        {
            SessionStatus.PENDING: frozenset(
                {SessionStatus.SCHEDULED, SessionStatus.EXPIRED}
            ),
            SessionStatus.SCHEDULED: frozenset(
                {
                    SessionStatus.CONFIRMED,
                    SessionStatus.COMPLETED,
                    SessionStatus.CANCELLED,
                    SessionStatus.NO_SHOW,
                }
            ),
            SessionStatus.CONFIRMED: frozenset(
                {
                    SessionStatus.COMPLETED,
                    SessionStatus.CANCELLED,
                    SessionStatus.NO_SHOW,
                }
            ),
            SessionStatus.NO_SHOW: frozenset({SessionStatus.SCHEDULED}),
            SessionStatus.CANCELLED: frozenset({SessionStatus.PENDING}),
            SessionStatus.COMPLETED: frozenset(),  # terminal
            SessionStatus.EXPIRED: frozenset(),  # terminal
        }
    )
)


class InvalidSessionTransitionError(Exception):
    def __init__(self, current: SessionStatus, target: SessionStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"transição inválida: {current} -> {target}")


def validate_transition(current: SessionStatus, target: SessionStatus) -> None:
    """Levanta InvalidSessionTransitionError se a transição não é
    permitida. Chamado pelo service antes de qualquer UPDATE — nunca
    confie que o chamador já validou."""
    if target == current:
        return
    allowed = SESSION_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidSessionTransitionError(current, target)
