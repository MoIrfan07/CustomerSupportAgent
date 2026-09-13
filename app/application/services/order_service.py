from app.domain.models import Order
from app.ports.order_port import OrderPort


class OrderService:
    """Application service for order-related use cases."""

    def __init__(self, order_port: OrderPort) -> None:
        self._order_port = order_port

    async def get_customer_orders(
        self,
        customer_id: str,
    ) -> list[Order]:
        """Retrieve all orders belonging to a customer."""

        return await self._order_port.get_customer_orders(customer_id)

    async def cancel_order(
        self,
        customer_id: str,
        order_id: str,
    ) -> Order:
        """
        Cancel an order through the order capability.

        The actual persistence/external-system operation is
        delegated to the configured port.
        """

        return await self._order_port.cancel_order(
            customer_id=customer_id,
            order_id=order_id,
        )
