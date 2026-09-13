from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.exceptions import PaymentNotRefundableError


class PaymentStatus(StrEnum):
    """Valid business states for a payment."""

    COMPLETED = "Completed"
    PENDING = "Pending"
    FAILED = "Failed"
    REFUNDED = "Refunded"


@dataclass(frozen=True, slots=True)
class Payment:
    """Core payment business entity."""

    payment_id: str
    customer_id: str
    amount: Decimal
    status: PaymentStatus

    def can_be_refunded(self) -> bool:
        """Return whether the payment is currently eligible for a refund."""

        return self.status is PaymentStatus.COMPLETED

    def refund(self) -> "Payment":
        """
        Refund the payment if the current business rules allow it.

        Returns:
            A new Payment with REFUNDED status.

        Raises:
            PaymentNotRefundableError:
                If the payment is not currently eligible for a refund.
        """

        if not self.can_be_refunded():
            raise PaymentNotRefundableError(
                payment_id=self.payment_id,
                current_status=self.status.value,
            )

        return Payment(
            payment_id=self.payment_id,
            customer_id=self.customer_id,
            amount=self.amount,
            status=PaymentStatus.REFUNDED,
        )
