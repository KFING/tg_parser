import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from src import log
from src.app_api.dependencies import DBM, get_db_main_manager


async def _wrapper(log_extra: dict[str, str], page_main: Callable[[DBM, dict[str, str]], Coroutine[Any, Any, None]]) -> None:
    dbm = get_db_main_manager()
    await page_main(dbm, log_extra)
    await dbm.close_connection()


def run_dash_page(mdl_name: str, page_main: Callable[[DBM, dict[str, str]], Coroutine[Any, Any, None]]) -> None:
    logger = logging.getLogger(mdl_name)
    with log.scope(logger, f"dash({mdl_name})") as log_extra:
        asyncio.run(_wrapper(log_extra, page_main))
