from types import MappingProxyType

from app.domain.retention.enums import ReturnOpportunityStatus


class InvalidReturnOpportunityTransitionError(ValueError):
    """Tentativa de transição proibida na máquina de estados de oportunidade."""


RETURN_OPPORTUNITY_TRANSITIONS: MappingProxyType[
    ReturnOpportunityStatus, frozenset[ReturnOpportunityStatus]
] = MappingProxyType(
    {
        ReturnOpportunityStatus.OPEN: frozenset(
            {
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.DISMISSED,
                ReturnOpportunityStatus.CLOSED,
            }
        ),
        ReturnOpportunityStatus.CONTACTED: frozenset(
            {
                ReturnOpportunityStatus.BOOKED,
                ReturnOpportunityStatus.DECLINED,
                ReturnOpportunityStatus.NO_RESPONSE,
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.DISMISSED,
                ReturnOpportunityStatus.CLOSED,
            }
        ),
        ReturnOpportunityStatus.NO_RESPONSE: frozenset(
            {
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.DISMISSED,
                ReturnOpportunityStatus.CLOSED,
            }
        ),
        ReturnOpportunityStatus.BOOKED: frozenset(
            {
                ReturnOpportunityStatus.CLOSED,
                ReturnOpportunityStatus.DISMISSED,
            }
        ),
        ReturnOpportunityStatus.DECLINED: frozenset(
            {
                ReturnOpportunityStatus.CLOSED,
                ReturnOpportunityStatus.DISMISSED,
            }
        ),
        ReturnOpportunityStatus.DISMISSED: frozenset(),
        ReturnOpportunityStatus.CLOSED: frozenset(),
    }
)


def validate_return_transition(
    current: ReturnOpportunityStatus, target: ReturnOpportunityStatus
) -> None:
    if current == target:
        return
    allowed = RETURN_OPPORTUNITY_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidReturnOpportunityTransitionError(
            f"Transição proibida: {current} -> {target}"
        )
