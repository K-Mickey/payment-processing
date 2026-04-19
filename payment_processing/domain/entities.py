from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID, uuid7

from payment_processing.domain.enums import CurrencyCode, PaymentStatus
from payment_processing.domain.errors import (
    AmountNegativeError,
    CurrencyNotSupportedError,
    StatusMustBePending,
    StatusNotSupportedError,
)


@dataclass(slots=True)
class Payment:
    payment_id: UUID
    amount: Decimal
    currency: CurrencyCode
    description: str
    metadata: dict
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        if self.amount <= 0:
            raise AmountNegativeError(self.amount)

        if self.currency not in CurrencyCode:
            raise CurrencyNotSupportedError(self.currency)

        if self.status not in PaymentStatus:
            raise StatusNotSupportedError(self.status)

        if type(self.webhook_url) is not str:
            raise TypeError("webhook_url must be a string")

    def is_pending(self) -> bool:
        return self.status == PaymentStatus.PENDING

    def success(self) -> None:
        if not self.is_pending():
            raise StatusMustBePending(self.status)

        self.status = PaymentStatus.SUCCESS
        self.processed_at = datetime.now(UTC)

    def fail(self) -> None:
        if not self.is_pending():
            raise StatusMustBePending(self.status)

        self.status = PaymentStatus.FAILED
        self.processed_at = datetime.now(UTC)

    @classmethod
    def create(
        cls,
        amount: Decimal,
        currency: CurrencyCode,
        description: str,
        metadata: dict,
        idempotency_key: str,
        webhook_url: str,
    ) -> Self:
        return cls(
            payment_id=uuid7(),
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=str(webhook_url),
            created_at=datetime.now(),
            processed_at=None,
        )

    def model_dump(self) -> dict:
        return asdict(self)
