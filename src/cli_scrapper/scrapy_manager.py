import logging
from datetime import datetime, timezone

from redis.asyncio import Redis

from src.parser_app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl
from src.common.moment import as_utc
from src.dto import redis_models
from src.dto.feed_rec_info import Source
from src.dto.scrappy_models import Post, Channel
from src.dto.tg_task import TgTaskStatus
from src.external_telegram import telegram_scrapy
from src.external_youtube import youtube_scrapy

logger = logging.getLogger(__name__)

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)
rds = Redis(host="redis", port=6379)


async def get_channel_info(source: Source, channel_name: str) -> Channel | None:
    match source:
        case Source.YOUTUBE:
            pass
        case Source.TELEGRAM:
            pass

async def get_progress_parsing(source: Source, channel_name: str, *, log_extra: dict[str, str]) -> int:
    dt_to = await rds.get(redis_models.source_channel_name_dt_to(source, channel_name))
    if not dt_to:
        return -1
    dt_from = await rds.get(redis_models.source_channel_name_dt_from(source, channel_name))
    if not dt_from:
        return -1
    dt_now = await rds.get(redis_models.source_channel_name_dt_now(source, channel_name))
    if not dt_now:
        return -1
    utc_dt_from = as_utc(datetime.fromisoformat(dt_from))
    utc_dt_to = datetime.fromisoformat(dt_to)
    utc_dt_now = as_utc(datetime.fromisoformat(dt_now))
    return int(((utc_dt_to - utc_dt_now) * 100) / (utc_dt_to - utc_dt_from))


async def start_parsing(source: Source, parsing_parameters: ParsingParametersApiMdl, *, log_extra: dict[str, str]):
    await rds.set(redis_models.source_channel_name_dt_to(source, parsing_parameters.channel_name), str(parsing_parameters.dt_to))
    await rds.set(redis_models.source_channel_name_dt_from(source, parsing_parameters.channel_name), str(parsing_parameters.dt_from))
    match source:
        case Source.YOUTUBE:
            tg_posts = [i async for i in await youtube_scrapy.get_channel_posts_list(parsing_parameters.channel_name, log_extra=log_extra)]
        case Source.TELEGRAM:
            tg_posts = await telegram_scrapy.get_channel_messages(parsing_parameters.channel_name, log_extra=log_extra)
        case _:
            return None
    if not isinstance(tg_posts, list):
        return None
    await rds.set(redis_models.source_channel_name_status(source, parsing_parameters.channel_name), TgTaskStatus.free.value)
    return tg_posts


async def stop_parsing(source: Source, parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.delete(redis_models.source_channel_name_dt_to(source, parsing_parameters.channel_name))
    await rds.delete(redis_models.source_channel_name_dt_from(source, parsing_parameters.channel_name))
    await rds.set(parsing_parameters.channel_name, TgTaskStatus.free.value)


async def change_params_parsing(source: Source, parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.set(redis_models.source_channel_name_dt_to(source, parsing_parameters.channel_name), str(parsing_parameters.dt_to))
    await rds.set(redis_models.source_channel_name_dt_from(source, parsing_parameters.channel_name), str(parsing_parameters.dt_from))
