from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Amount must be greater than 0")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    def is_final(self) -> bool:
        return self in {PaymentStatus.SUCCESS, PaymentStatus.FAILED}

    def can_transition_to(self, target: Self) -> bool:
        allowed = {
            PaymentStatus.PENDING: {PaymentStatus.SUCCESS, PaymentStatus.FAILED},
            PaymentStatus.SUCCESS: {},
            PaymentStatus.FAILED: {},
        }
        return target in allowed[self]


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    value: str

    def __post_init__(self):
        if not self.value.strip():
            raise ValueError("Idempotency key must not be empty")


@dataclass(frozen=True, slots=True)
class WebhookUrl:
    url: str

    def __post_init__(self):
        parsed = urlparse(self.url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL {self.url}")

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Invalid scheme in URL {self.url}")


@dataclass(frozen=True, slots=True)
class Metadata:
    data: dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.data, dict):
            raise ValueError("Metadata must be a dictionary")
