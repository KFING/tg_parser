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

logger = logging.getLogger(__name__)


tg_parser_router = APIRouter(
    tags=["tg parser"],
)
rds = Redis()



@tg_parser_router.post("/add")
async def start(parsing_parameters: ParsingParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> int:
    await rds.set(parsing_parameters.name, str(parsing_parameters.dt_to))
    await rds.set(parsing_parameters.name, str(parsing_parameters.dt_from))
    return 0

@tg_parser_router.patch("/change")
async def stop(parsing_parameters: ParsingParametersApiMdl) -> None:
    await rds.set(parsing_parameters.name, str(parsing_parameters.dt_to))
    await rds.set(parsing_parameters.name, str(parsing_parameters.dt_from))
    return

@tg_parser_router.get("/progress")
async def get_progress(token: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return

@tg_parser_router.delete("/stop")
async def logout(token: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return





