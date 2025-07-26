import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from src import log


async def _wrapper(log_extra: dict[str, str], page_main: Callable[dict[str, str], Coroutine[Any, Any, None]]) -> None:
    await page_main(log_extra)


def run_dash_page(mdl_name: str, page_main: Callable[dict[str, str], Coroutine[Any, Any, None]]) -> None:
    logger = logging.getLogger(mdl_name)
    with log.scope(logger, f"dash({mdl_name})") as log_extra:
        asyncio.run(_wrapper(log_extra, page_main))
