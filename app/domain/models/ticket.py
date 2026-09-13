from dataclasses import dataclass
from enum import StrEnum


class TicketStatus(StrEnum):
    """Valid business states for a support ticket."""

    OPEN = "Open"
    CLOSED = "Closed"


class TicketPriority(StrEnum):
    """Valid support ticket priorities."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass(frozen=True, slots=True)
class SupportTicket:
    """Core support ticket business entity."""

    ticket_id: str
    customer_id: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
