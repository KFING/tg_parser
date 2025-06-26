import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_api.dependencies import get_db_main
from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models import feed_rec_request_info
from src.app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl
from src.db_main.cruds import tg_post_crud
from src.db_main.models.tg_post import TgPostDbMdl
from src.external_telegram import telegram_scrapy

logger = logging.getLogger(__name__)


tg_parser_router = APIRouter(
    tags=["tg parser"],
)
rds = Redis()



@tg_parser_router.post("/add")
async def start(parsing_parameters: ParsingParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra), db: AsyncSession = Depends(get_db_main)) -> int:
    await rds.set(f'{parsing_parameters.channel_name}_dt_to', str(parsing_parameters.dt_to))
    await rds.set(f'{parsing_parameters.channel_name}_dt_from', str(parsing_parameters.dt_from))
    tg_posts = await telegram_scrapy.get_channel_messages(parsing_parameters.channel_name, parsing_parameters.dt_to, parsing_parameters.dt_from, log_extra=log_extra)
    id_posts = await tg_post_crud.get_all_id_posts(db)
    new_posts: list[TgPostDbMdl] = []
    for tg_post in tg_posts:
        if tg_post.id not in id_posts:
            new_posts.append(tg_post)
    await tg_post_crud.create_tg_posts(db, new_posts)
    return 0

@tg_parser_router.patch("/change")
async def stop(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.delete(f'{parsing_parameters.channel_name}_dt_to')
    await rds.delete(f'{parsing_parameters.channel_name}_dt_from')
    return

@tg_parser_router.get("/progress")
async def get_progress(token: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return

@tg_parser_router.delete("/stop")
async def change_params(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.set(f'{parsing_parameters.channel_name}_dt_to', str(parsing_parameters.dt_to))
    await rds.set(f'{parsing_parameters.channel_name}_dt_from', str(parsing_parameters.dt_from))
    return





