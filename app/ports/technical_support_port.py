from typing import Protocol

from app.domain.models import SupportTicket


class TechnicalSupportPort(Protocol):
    """Port for customer technical support information."""

    async def get_customer_tickets(
        self,
        customer_id: str,
    ) -> list[SupportTicket]:
        """Retrieve support tickets belonging to a customer."""
        ...
