from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from payment_processing.domain import Payment


@dataclass(frozen=True, slots=True)
class PaymentDTO:
    payment_id: UUID
    amount: Decimal
    currency: str
    description: str
    metadata: dict
    status: str
    idempotency_key: str
    created_at: datetime
    processed_at: datetime | None
    webhook_url: str

    @classmethod
    def from_entity(cls, payment: Payment) -> Self:
        return cls(
            payment_id=payment.id,
            amount=payment.amount.amount,
            currency=payment.amount.currency,
            description=payment.description,
            metadata=payment.metadata.data,
            status=payment.status.value,
            idempotency_key=payment.idempotency_key.value,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
            webhook_url=payment.webhook_url.url,
        )
