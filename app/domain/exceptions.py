class DomainError(Exception):
    """Base exception for business rule violations."""


class OrderNotCancellableError(DomainError):
    """Raised when an order cannot be cancelled."""

    def __init__(self, order_id: str, current_status: str) -> None:
        self.order_id = order_id
        self.current_status = current_status

        super().__init__(
            f"Order {order_id} cannot be cancelled because "
            f"its current status is {current_status}."
        )


class PaymentNotRefundableError(DomainError):
    """Raised when a payment cannot be refunded."""

    def __init__(self, payment_id: str, current_status: str) -> None:
        self.payment_id = payment_id
        self.current_status = current_status

        super().__init__(
            f"Payment {payment_id} cannot be refunded because "
            f"its current status is {current_status}."
        )
