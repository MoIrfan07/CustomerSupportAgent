from app.domain.models import (
    SupportTicket,
    TicketPriority,
    TicketStatus,
)
from app.ports.technical_support_port import TechnicalSupportPort


class InMemoryTechnicalSupportAdapter(TechnicalSupportPort):
    """In-memory implementation of the technical-support port."""

    def __init__(
        self,
        tickets: dict[str, list[dict]],
    ) -> None:
        self._tickets = tickets

    async def get_customer_tickets(
        self,
        customer_id: str,
    ) -> list[SupportTicket]:
        customer_tickets = self._tickets.get(customer_id, [])

        return [
            SupportTicket(
                ticket_id=str(item["ticket_id"]),
                customer_id=customer_id,
                subject=str(item["subject"]),
                status=TicketStatus(item["status"]),
                priority=TicketPriority(item["priority"]),
            )
            for item in customer_tickets
        ]
