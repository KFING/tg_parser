import logging

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_api.dependencies import get_db_main
from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl
from src.dto.tg_post import TgPost
from src.external_telegram import scrapy_manager

logger = logging.getLogger(__name__)


tg_parser_router = APIRouter(
    tags=["tg parser"],
)
rds = Redis()


@tg_parser_router.post("/start")
async def start_parser(
    parsing_parameters: ParsingParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra), db: AsyncSession = Depends(get_db_main)
) -> list[TgPost] | None:
    return await scrapy_manager.start_parsing(db, parsing_parameters, log_extra=log_extra)


@tg_parser_router.delete("/stop")
async def stop_parser(parsing_parameters: ParsingParametersApiMdl) -> None:
    await scrapy_manager.stop_parsing(parsing_parameters)


@tg_parser_router.get("/progress")
async def get_progress(channel_name: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    await scrapy_manager.get_progress_parsing(channel_name, log_extra=log_extra)


@tg_parser_router.patch("/change")
async def change_params_parser(parsing_parameters: ParsingParametersApiMdl) -> None:
    await scrapy_manager.change_params_parsing(parsing_parameters)
