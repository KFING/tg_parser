import logging

from fastapi import FastAPI

from src.errors import ApiError, api_error_handler
from src.parser_app_api.middlewares import log_extra_middleware
from src.parser_app_api.routes.telegram_router import tg_parser_router
from src.parser_app_api.routes.youtube_router import yt_parser_router

logger = logging.getLogger(__name__)


def get_app() -> FastAPI:
    # init
    app = FastAPI()

    # routes
    app.include_router(tg_parser_router)
    app.include_router(yt_parser_router)

    # middlewares
    app.middleware("http")(log_extra_middleware)

    # exception handlers
    app.add_exception_handler(exc_class_or_status_code=ApiError, handler=api_error_handler)

    # other

    return app
