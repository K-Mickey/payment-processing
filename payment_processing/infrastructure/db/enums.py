from enum import StrEnum


class AggregateType(StrEnum):
    PAYMENT = "payment"


class RoutingKey(StrEnum):
    PAYMENT_NEW = "payment.new"
