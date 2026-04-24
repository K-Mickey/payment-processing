from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Self
from uuid import UUID

from payment_processing.domain.value_objects import Currency, IdempotencyKey, Metadata, Money, PaymentStatus, WebhookUrl
from payment_processing.utils import datetime_now, uuid


@dataclass
class Payment:
    id: UUID
    amount: Money
    description: str
    metadata: Metadata
    idempotency_key: IdempotencyKey
    webhook_url: WebhookUrl
    status: PaymentStatus
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def create(
        cls,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: dict[str, Any],
        idempotency_key: str,
        webhook_url: str,
    ) -> Self:

        return cls(
            id=uuid(),
            amount=Money(amount, currency),
            description=description,
            metadata=Metadata(metadata),
            idempotency_key=IdempotencyKey(idempotency_key),
            webhook_url=WebhookUrl(webhook_url),
            status=PaymentStatus.PENDING,
            created_at=datetime_now(),
            processed_at=None,
        )

    def mark_as_succeeded(self) -> None:
        self._change_status(PaymentStatus.SUCCESS)
        self.processed_at = datetime_now()

    def mark_as_failed(self) -> None:
        self._change_status(PaymentStatus.FAILED)
        self.processed_at = datetime_now()

    def _change_status(self, new_status: PaymentStatus) -> None:
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status.value} to {new_status.value}")
        self.status = new_status

    @property
    def is_processed(self) -> bool:
        return self.status.is_final()
