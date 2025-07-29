import asyncio
import logging
import time

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl
from src.cli_scrapper import scrapy_manager
from src.dto.feed_rec_info import Source
from src.dto.post import Post

logger = logging.getLogger(__name__)


yt_parser_router = APIRouter(
    tags=["youtube parser"],
)

@yt_parser_router.post("/start_youtube_parser")
async def start_parser(
    parsing_parameters: ParsingParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> list[Post] | None:
    return await scrapy_manager.start_parsing(Source.YOUTUBE, parsing_parameters, log_extra=log_extra)


@yt_parser_router.delete("/stop_youtube_parser")
async def stop_parser(parsing_parameters: ParsingParametersApiMdl) -> None:
    await scrapy_manager.stop_parsing(Source.YOUTUBE, parsing_parameters)


@yt_parser_router.get("/progress_youtube_parser")
async def get_progress(channel_name: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    await scrapy_manager.get_progress_parsing(Source.YOUTUBE, channel_name, log_extra=log_extra)


@yt_parser_router.patch("/change_youtube_parser")
async def change_params_parser(parsing_parameters: ParsingParametersApiMdl) -> None:
    await scrapy_manager.change_params_parsing(Source.YOUTUBE, parsing_parameters)
