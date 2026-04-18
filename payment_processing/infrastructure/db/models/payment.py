from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from payment_processing.domain.enums import CurrencyCode, PaymentStatus
from payment_processing.infrastructure.db.models.base import Base


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_payments_idempotency_key", "idempotency_key", unique=True),
    )

    payment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[CurrencyCode] = mapped_column(Enum(CurrencyCode), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    payment_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    webhook_url: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @classmethod
    def create(cls, **kwargs):
        if "metadata" in kwargs:
            kwargs["payment_metadata"] = kwargs.pop("metadata")
        return cls(**kwargs)
