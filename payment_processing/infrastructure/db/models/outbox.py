from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import DateTime, Enum, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from payment_processing.infrastructure.db.models.base import Base
from payment_processing.infrastructure.messaging import AggregateType, TopicType


class Outbox(Base):
    __tablename__ = "outbox"
    __table_args__ = (Index("ix_outbox_published_at_created_at", "published_at", "created_at"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )
    aggregate_type: Mapped[AggregateType] = mapped_column(Enum(AggregateType), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    topic: Mapped[TopicType] = mapped_column(Enum(TopicType), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
