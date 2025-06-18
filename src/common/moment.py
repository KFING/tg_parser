from copy import copy
from datetime import datetime, timezone

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return copy(dt).replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def select_max_dt(*args: datetime) -> datetime:
    assert len(args) > 0
    max_dt = args[0]
    for dt in args[1:]:
        if as_utc(dt) > as_utc(max_dt):
            max_dt = dt
    return max_dt


def test_select_max_dt() -> None:
    assert as_utc(datetime(2024, 1, 1)) == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert as_utc(datetime(2024, 1, 1)) == as_utc(datetime(2024, 1, 1, tzinfo=timezone.utc))
    assert select_max_dt(
        datetime(2024, 1, 1),
    ) == datetime(2024, 1, 1)
    assert select_max_dt(
        datetime(2022, 1, 1),
        datetime(2024, 1, 1),
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 1),
    ) == datetime(2024, 1, 1)
