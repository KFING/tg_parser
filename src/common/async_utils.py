import asyncio
import logging
from collections.abc import Callable, Coroutine
from functools import partial, wraps
from typing import Any, Final, TypeVar

from typing_extensions import ParamSpec

logger: Final = logging.getLogger(__name__)

_T = TypeVar("_T")
_P = ParamSpec("_P")
_TP = ParamSpec("_TP")
_TR = TypeVar("_TR")
TR = TypeVar("TR")


def sync_to_async(func: Callable[_P, _T]) -> Callable[_P, Coroutine[Any, Any, _T]]:
    """Creates a coroutine from a synchronous function."""

    @wraps(func)
    async def _sync_to_async(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    return _sync_to_async


async def run_list(tasks: list[Coroutine[None, None, TR]], size: int) -> list[TR]:
    results = []
    for i in range(0, len(tasks), size):
        chunk = tasks[i * size : (i + 1) * size]
        results += list(await asyncio.gather(*chunk))
    return results


def run_on_loop(some: Coroutine[Any, Any, _TR]) -> _TR:
    try:
        loop = asyncio.get_event_loop()
    except Exception:
        loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(some)
    except RuntimeError:
        future = asyncio.run_coroutine_threadsafe(some, loop)
        return future.result()
