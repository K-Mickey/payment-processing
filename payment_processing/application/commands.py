from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CreatePaymentCommand:
    amount: Decimal
    currency: str
    description: str
    metadata: dict
    idempotency_key: str
    webhook_url: str
