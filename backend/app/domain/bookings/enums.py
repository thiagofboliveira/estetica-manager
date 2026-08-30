from enum import StrEnum


class BookingStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    CONVERTED = "CONVERTED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
