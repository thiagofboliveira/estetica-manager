from types import MappingProxyType

from app.domain.bookings.enums import BookingStatus


class InvalidBookingTransitionError(ValueError):
    """Tentativa de transição proibida na máquina de estados de booking."""


BOOKING_TRANSITIONS: MappingProxyType[BookingStatus, frozenset[BookingStatus]] = (
    MappingProxyType(
        {
            BookingStatus.SCHEDULED: frozenset(
                {
                    BookingStatus.SCHEDULED,  # reagendamento
                    BookingStatus.CONVERTED,
                    BookingStatus.CANCELLED,
                    BookingStatus.NO_SHOW,
                }
            ),
            BookingStatus.CONVERTED: frozenset(),  # terminal
            BookingStatus.CANCELLED: frozenset(),  # terminal
            BookingStatus.NO_SHOW: frozenset(
                {BookingStatus.SCHEDULED}
            ),  # reagendar após no-show
        }
    )
)


def validate_booking_transition(current: BookingStatus, target: BookingStatus) -> None:
    if current == target:
        return
    allowed = BOOKING_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidBookingTransitionError(
            f"Transição de booking proibida: {current} -> {target}"
        )
