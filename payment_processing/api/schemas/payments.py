from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from payment_processing.domain import Currency, PaymentStatus


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(..., title="Payment amount", examples=["100.00"], gt=0, max_digits=18, decimal_places=2)
    currency: Currency = Field(..., title="Payment currency", examples=list(Currency))
    description: str = Field(default="", title="Payment description", examples=["Payment for order #123"])
    metadata: dict | None = Field(default_factory=dict, title="Payment metadata", examples=[{"order_id": "123"}])
    webhook_url: HttpUrl = Field(..., title="Payment webhook URL", examples=["https://example.com/webhook"])


class CreatePaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    payment_id: UUID = Field(title="Payment ID", examples=["1e4e5e6e-7e8e-9e9e-aeae-1e2e3e4e5e6e"])
    status: PaymentStatus = Field(title="Payment status", examples=list(PaymentStatus))
    created_at: datetime = Field(title="Payment created at", examples=["2021-01-01T00:00:00Z"])


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_id: UUID = Field(title="Payment ID", examples=["1e4e5e6e-7e8e-9e9e-aeae-1e2e3e4e5e6e"])
    amount: Decimal = Field(title="Payment amount", examples=["100.00"])
    currency: Currency = Field(title="Payment currency", examples=list(Currency))
    description: str = Field(title="Payment description", examples=["Payment for order #123"])
    metadata: dict = Field(title="Payment metadata", examples=[{"order_id": "123"}])
    status: PaymentStatus = Field(title="Payment status", examples=list(PaymentStatus))
    idempotency_key: str = Field(title="Payment idempotency key", examples=["1e4e5e6e-7e8e-9e9e-aeae-1e2e3e4e5e6e"])
    webhook_url: str = Field(title="Payment webhook URL", examples=["https://example.com/webhook"])
    created_at: datetime = Field(title="Payment created at", examples=["2021-01-01T00:00:00Z"])
    processed_at: datetime | None = Field(title="Payment processed at", examples=["2021-01-01T00:00:00Z"])
