from decimal import Decimal
from uuid import UUID


class DomainError(Exception):
    pass


class AmountNegativeError(DomainError):
    def __init__(self, amount: Decimal):
        self.message = f"Amount must be greater than 0, got {amount}"


class CurrencyNotSupportedError(DomainError):
    def __init__(self, currency: str):
        self.message = f"Currency must be one of the supported currencies, got {currency}"


class StatusNotSupportedError(DomainError):
    def __init__(self, status: str):
        self.message = f"Status must be one of the supported statuses, got {status}"


class StatusMustBePending(DomainError):
    def __init__(self, status: str):
        self.message = f"Cannot complete a payment that is not pending, got {status}"


class PaymentNotFoundError(DomainError):
    def __init__(self, payment_id: UUID):
        self.message = f"Payment {payment_id} not found"


class PaymentAlreadyExistsError(DomainError):
    def __init__(self, payment_id: UUID):
        self.message = f"Payment {payment_id} already exists"
