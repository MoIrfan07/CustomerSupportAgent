from dataclasses import dataclass
from enum import StrEnum


class CustomerStatus(StrEnum):
    """Valid business states for a customer account."""

    ACTIVE = "Active"
    SUSPENDED = "Suspended"


@dataclass(frozen=True, slots=True)
class Customer:
    """Core customer business entity."""

    customer_id: str
    name: str
    email: str
    status: CustomerStatus
    plan: str
