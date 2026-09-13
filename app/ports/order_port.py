from typing import Protocol

from app.domain.models import Order


class OrderPort(Protocol):
    """Port for retrieving and operating on customer orders."""

    async def get_customer_orders(
        self,
        customer_id: str,
    ) -> list[Order]:
        """Retrieve all orders belonging to a customer."""
        ...

    async def cancel_order(
        self,
        customer_id: str,
        order_id: str,
    ) -> Order:
        """Cancel a customer order."""
        ...
