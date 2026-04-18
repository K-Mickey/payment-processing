from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID, uuid7

from payment_processing.infrastructure.messaging.enums import AggregateType, TopicType


@dataclass(slots=True)
class Outbox:
    id: UUID
    aggregate_type: AggregateType
    aggregate_id: UUID
    topic: TopicType
    payload: dict
    headers: dict
    created_at: datetime
    published_at: datetime | None
    last_error: str | None

    @classmethod
    def create(
        cls,
        aggregate_type: AggregateType,
        aggregate_id: UUID,
        topic: TopicType,
        payload: dict,
        headers: dict,
    ):
        return cls(
            id=uuid7(),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            topic=topic,
            payload=payload,
            headers=headers,
            created_at=datetime.now(),
            published_at=None,
            last_error=None,
        )

    def model_dump(self):
        return asdict(self)
