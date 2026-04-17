from enum import StrEnum


class AggregateType(StrEnum):
    PAYMENT = "payment"


class TopicType(StrEnum):
    PAYMENT_NEW = "payment.new"
