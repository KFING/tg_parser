import logging

from fastapi import APIRouter, Depends

from src.cli_scrapper import scrapy_manager
from src.dto.feed_rec_info import Source
from src.parser_app_api.middlewares import get_log_extra
from src.parser_app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl, InfoParsingParametersApiMdl

logger = logging.getLogger(__name__)


parser_router = APIRouter(
    tags=["parser router"],
)


@parser_router.post("/start_parser")
async def start_parser(parsing_parameters: ParsingParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)):
    return await scrapy_manager.start_parsing(parsing_parameters, log_extra=log_extra)


@parser_router.delete("/stop_parser")
async def stop_parser(info_parsing_parameters: InfoParsingParametersApiMdl) -> None:
    await scrapy_manager.stop_parsing(info_parsing_parameters)


@parser_router.get("/progress_parser")
async def get_progress(info_parsing_parameters: InfoParsingParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    await scrapy_manager.get_progress_parsing(info_parsing_parameters, log_extra=log_extra)


@parser_router.patch("/change_parser")
async def change_params_parser(parsing_parameters: ParsingParametersApiMdl) -> None:
    await scrapy_manager.change_params_parsing(parsing_parameters)
