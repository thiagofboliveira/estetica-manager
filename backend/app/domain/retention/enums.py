from enum import StrEnum


class ReturnOpportunityStatus(StrEnum):
    OPEN = "OPEN"
    CONTACTED = "CONTACTED"
    BOOKED = "BOOKED"
    DECLINED = "DECLINED"
    NO_RESPONSE = "NO_RESPONSE"
    DISMISSED = "DISMISSED"
    CLOSED = "CLOSED"


class ContactChannel(StrEnum):
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    IN_PERSON = "IN_PERSON"
    OTHER = "OTHER"


class Timing(StrEnum):
    UPCOMING = "UPCOMING"
    DUE = "DUE"
    OVERDUE = "OVERDUE"
