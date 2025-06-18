import uuid

from sqlalchemy.dialects.postgresql import UUID


def as_uuid(value: str | uuid.UUID | UUID[uuid.UUID]) -> uuid.UUID:
    return uuid.UUID(str(value)) if not isinstance(value, uuid.UUID) else value
