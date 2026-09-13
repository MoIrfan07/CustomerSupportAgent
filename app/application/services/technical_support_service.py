from app.domain.models import SupportTicket
from app.ports.technical_support_port import TechnicalSupportPort


class TechnicalSupportService:
    """Application service for technical-support use cases."""

    def __init__(
        self,
        technical_support_port: TechnicalSupportPort,
    ) -> None:
        self._technical_support_port = technical_support_port

    async def get_customer_tickets(
        self,
        customer_id: str,
    ) -> list[SupportTicket]:
        """Retrieve support tickets belonging to a customer."""

        return await self._technical_support_port.get_customer_tickets(customer_id)
