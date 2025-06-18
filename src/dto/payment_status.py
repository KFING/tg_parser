from enum import Enum


class PaymentStatus(Enum):
    PAID = "PAID"
    CANCELED_FULL = "CANCELED_FULL"
    CANCELED_PARTIAL = "CANCELED_PARTIAL"
