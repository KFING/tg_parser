import asyncio
import logging
from collections.abc import Callable, Coroutine
from functools import partial, wraps
from typing import Any, Final, TypeVar

from typing_extensions import ParamSpec

logger: Final = logging.getLogger(__name__)

_T = TypeVar("_T")
_P = ParamSpec("_P")


def sync_to_async(func: Callable[_P, _T]) -> Callable[_P, Coroutine[Any, Any, _T]]:
    """Creates a coroutine from a synchronous function."""

    @wraps(func)
    async def _sync_to_async(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    return _sync_to_async


TR = TypeVar("TR")


async def run_list(tasks: list[Coroutine[None, None, TR]], size: int) -> list[TR]:
    results = []
    for i in range(0, len(tasks), size):
        chunk = tasks[i * size : (i + 1) * size]
        results += list(await asyncio.gather(*chunk))
    return results
