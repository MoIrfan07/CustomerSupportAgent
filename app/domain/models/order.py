from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.exceptions import OrderNotCancellableError


class OrderStatus(StrEnum):
    """Valid business states for an order."""

    DELIVERED = "Delivered"
    PROCESSING = "Processing"
    CANCELLED = "Cancelled"


@dataclass(frozen=True, slots=True)
class Order:
    """Core order business entity."""

    order_id: str
    customer_id: str
    product: str
    amount: Decimal
    status: OrderStatus

    def can_be_cancelled(self) -> bool:
        """Return whether the order is currently eligible for cancellation."""

        return self.status is OrderStatus.PROCESSING

    def cancel(self) -> "Order":
        """
        Cancel the order if the current business rules allow it.

        Returns:
            A new Order with CANCELLED status.

        Raises:
            OrderNotCancellableError:
                If the order is not currently eligible for cancellation.
        """

        if not self.can_be_cancelled():
            raise OrderNotCancellableError(
                order_id=self.order_id,
                current_status=self.status.value,
            )

        return Order(
            order_id=self.order_id,
            customer_id=self.customer_id,
            product=self.product,
            amount=self.amount,
            status=OrderStatus.CANCELLED,
        )
