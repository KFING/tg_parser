import uuid

from src.common.typing import as_uuid


def test_as_uuid() -> None:
    assert uuid.UUID("3140ff58-7378-4506-bf0a-c2184226408a") == as_uuid("3140ff58-7378-4506-bf0a-c2184226408a")
    assert uuid.UUID("3140ff58-7378-4506-bf0a-c2184226408a") == as_uuid(uuid.UUID("3140ff58-7378-4506-bf0a-c2184226408a"))
