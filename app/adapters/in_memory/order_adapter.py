from decimal import Decimal

from app.domain.models import Order, OrderStatus
from app.ports.order_port import OrderPort


class InMemoryOrderAdapter(OrderPort):
    """In-memory implementation of the order port."""

    def __init__(self, orders: dict[str, list[dict]]) -> None:
        self._orders = orders

    async def get_customer_orders(
        self,
        customer_id: str,
    ) -> list[Order]:
        customer_orders = self._orders.get(customer_id, [])

        return [
            Order(
                order_id=str(item["order_id"]),
                customer_id=customer_id,
                product=str(item["product"]),
                amount=Decimal(str(item["amount"])),
                status=OrderStatus(item["status"]),
            )
            for item in customer_orders
        ]

    async def cancel_order(
        self,
        customer_id: str,
        order_id: str,
    ) -> Order:
        customer_orders = self._orders.get(customer_id, [])

        order = next(
            (item for item in customer_orders if item["order_id"] == order_id),
            None,
        )

        if order is None:
            raise ValueError(
                f"Order {order_id} was not found for customer {customer_id}."
            )

        if order["status"] != "Processing":
            raise ValueError(
                f"Order {order_id} cannot be cancelled because "
                f"its current status is {order['status']}."
            )

        order["status"] = "Cancelled"

        return Order(
            order_id=str(order["order_id"]),
            customer_id=customer_id,
            product=str(order["product"]),
            amount=Decimal(str(order["amount"])),
            status=OrderStatus(order["status"]),
        )
