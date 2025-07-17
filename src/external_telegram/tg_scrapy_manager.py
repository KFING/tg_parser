import logging
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl
from src.common.moment import as_utc
from src.db_main.cruds import tg_post_crud
from src.db_main.models.tg_post import TgPostDbMdl
from src.dto import redis_models
from src.dto.feed_rec_info import Source
from src.dto.tg_post import TgPost
from src.dto.tg_task import TgTaskStatus
from src.external_telegram import telegram_scrapy

logger = logging.getLogger(__name__)

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)
rds = Redis(host='redis', port=6379)


async def get_progress_parsing(channel_name: str, *, log_extra: dict[str, str]) -> int:
    if not await rds.get(redis_models.source_channel_name_dt_from(Source.TELEGRAM, channel_name)):
        return -1
    if not await rds.get(redis_models.source_channel_name_dt_to(Source.TELEGRAM, channel_name)):
        return -1
    if not await rds.get(redis_models.source_channel_name_dt_now(Source.TELEGRAM, channel_name)):
        return -1
    utc_dt_from = as_utc(datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_from(Source.TELEGRAM, channel_name))))
    utc_dt_to = datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_to(Source.TELEGRAM, channel_name)))
    utc_dt_now = as_utc(datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_now(Source.TELEGRAM, channel_name))))
    return int(((utc_dt_to - utc_dt_now) * 100) / (utc_dt_to - utc_dt_from))


async def start_parsing(parsing_parameters: ParsingParametersApiMdl, *, log_extra: dict[str, str]) -> list[TgPost] | None:
    await rds.set(redis_models.source_channel_name_dt_to(Source.TELEGRAM, parsing_parameters.channel_name), str(parsing_parameters.dt_to))
    await rds.set(redis_models.source_channel_name_dt_from(Source.TELEGRAM, parsing_parameters.channel_name), str(parsing_parameters.dt_from))
    tg_posts = await telegram_scrapy.get_channel_messages(
        parsing_parameters.channel_name, log_extra=log_extra
    )
    if not isinstance(tg_posts, list):
        return None
    await rds.set(parsing_parameters.channel_name, TgTaskStatus.free.value)
    return tg_posts


async def stop_parsing(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.delete(redis_models.source_channel_name_dt_to(Source.TELEGRAM, parsing_parameters.channel_name))
    await rds.delete(redis_models.source_channel_name_dt_from(Source.TELEGRAM, parsing_parameters.channel_name))
    await rds.set(parsing_parameters.channel_name, TgTaskStatus.free.value)


async def change_params_parsing(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.set(redis_models.source_channel_name_dt_to(Source.TELEGRAM, parsing_parameters.channel_name), str(parsing_parameters.dt_to))
    await rds.set(redis_models.source_channel_name_dt_from(Source.TELEGRAM, parsing_parameters.channel_name), str(parsing_parameters.dt_from))
