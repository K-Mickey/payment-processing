from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from payment_processing.domain import CurrencyCode


@dataclass(frozen=True, slots=True)
class PaymentPayload:
    payment_id: UUID
    status: str
    amount: Decimal
    currency: CurrencyCode
