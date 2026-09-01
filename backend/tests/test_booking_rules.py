import pytest

from app.domain.bookings.enums import BookingStatus
from app.domain.bookings.state_machine import (
    InvalidBookingTransitionError,
    validate_booking_transition,
)


def test_booking_state_machine_valid() -> None:
    validate_booking_transition(BookingStatus.SCHEDULED, BookingStatus.CONVERTED)
    validate_booking_transition(BookingStatus.SCHEDULED, BookingStatus.CANCELLED)
    validate_booking_transition(BookingStatus.SCHEDULED, BookingStatus.NO_SHOW)
    validate_booking_transition(BookingStatus.NO_SHOW, BookingStatus.SCHEDULED)


def test_booking_state_machine_invalid() -> None:
    with pytest.raises(InvalidBookingTransitionError):
        validate_booking_transition(BookingStatus.CONVERTED, BookingStatus.SCHEDULED)

    with pytest.raises(InvalidBookingTransitionError):
        validate_booking_transition(BookingStatus.CANCELLED, BookingStatus.SCHEDULED)
