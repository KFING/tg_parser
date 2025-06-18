from enum import Enum


class PaymentMethod(Enum):
    PADDLE = "PADDLE"


class RefundItemType(Enum):
    partial = "partial"
    full = "full"


class PaymentComment(Enum):
    canceled = "canceled"
    paid = "paid"
