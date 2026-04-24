from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from payment_processing.domain.entities import Payment


class PaymentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment | None: ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Payment | None: ...

    @abstractmethod
    async def save(self, payment: Payment) -> Payment: ...


class OutboxRepository(ABC):
    @abstractmethod
    async def add_payment_created(self, payment: Payment) -> object: ...

    @abstractmethod
    async def fetch_pending_events(self, limit: int = 10) -> Sequence[object]: ...


class UnitOfWork(ABC):
    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    @abstractmethod
    async def commit(self): ...

    @abstractmethod
    async def rollback(self): ...


class PaymentProcessor(ABC):
    @abstractmethod
    async def process(self, payment: Payment) -> bool: ...


class WebhookNotifier(ABC):
    @abstractmethod
    async def notify(self, payment_id: UUID, status: str, webhook_url: str) -> None: ...
