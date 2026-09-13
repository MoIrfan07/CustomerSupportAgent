from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class InvoiceStatus(StrEnum):
    """Valid business states for an invoice."""

    PAID = "Paid"
    PENDING = "Pending"
    OVERDUE = "Overdue"


@dataclass(frozen=True, slots=True)
class Invoice:
    """Core invoice business entity."""

    invoice_id: str
    customer_id: str
    amount: Decimal
    status: InvoiceStatus
