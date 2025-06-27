import asyncio
import logging

import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime, timezone

from pydantic import HttpUrl
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl
from src.common.moment import as_utc
from src.db_main.cruds import tg_post_crud
from src.db_main.models.tg_post import TgPostDbMdl
from src.dto.tg_post import TgPost
from src.dto.tg_task import TgTaskStatus
from src.env import SCRAPPER_RESULTS_DIR_TELEGRAM_RAW
from src.external_telegram import telegram_scrapy

logger = logging.getLogger(__name__)

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)
rds = Redis()

async def get_progress_parsing(channel_name: str, *, log_extra: dict[str, str]) -> int:
    if not await rds.get(f'{channel_name}_dt_to'):
        return -1
    if not await rds.get(f'{channel_name}_dt_from'):
        return -1
    if not await rds.get(f'{channel_name}_dt_now'):
        return -1
    utc_dt_from = as_utc(datetime.fromisoformat(await rds.get(f'{channel_name}_dt_from')))
    utc_dt_to = datetime.fromisoformat(await rds.get(f'{channel_name}_dt_to'))
    utc_dt_now = as_utc(datetime.fromisoformat(await rds.get(f'{channel_name}_dt_now')))
    return int(((utc_dt_to - utc_dt_now) * 100) / (utc_dt_to - utc_dt_from))

async def start_parsing(db: AsyncSession, parsing_parameters: ParsingParametersApiMdl, *, log_extra: dict[str, str]) -> None:
    await rds.set(f'{parsing_parameters.channel_name}_dt_to', str(parsing_parameters.dt_to))
    await rds.set(f'{parsing_parameters.channel_name}_dt_from', str(parsing_parameters.dt_from))
    tg_posts = await telegram_scrapy.get_channel_messages(parsing_parameters.channel_name, parsing_parameters.dt_to, parsing_parameters.dt_from, log_extra=log_extra)
    id_posts = await tg_post_crud.get_all_id_posts(db)
    new_posts: list[TgPostDbMdl] = []
    for tg_post in tg_posts:
        if tg_post.id not in id_posts:
            new_posts.append(tg_post)
    await tg_post_crud.create_tg_posts(db, new_posts)
    await rds.set(parsing_parameters.channel_name, TgTaskStatus.free.value)

async def stop_parsing(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.delete(f'{parsing_parameters.channel_name}_dt_to')
    await rds.delete(f'{parsing_parameters.channel_name}_dt_from')
    await rds.set(parsing_parameters.channel_name, TgTaskStatus.free.value)

async def change_params_parsing(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.set(f'{parsing_parameters.channel_name}_dt_to', str(parsing_parameters.dt_to))
    await rds.set(f'{parsing_parameters.channel_name}_dt_from', str(parsing_parameters.dt_from))
