from datetime import UTC, datetime
from uuid import UUID, uuid7


def uuid() -> UUID:
    return uuid7()


def datetime_now() -> datetime:
    return datetime.now(UTC)
