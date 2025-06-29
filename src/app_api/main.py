import logging

from fastapi import FastAPI

from src.app_api.middlewares import log_extra_middleware
from src.app_api.routes.tg_parser_router import tg_parser_router
from src.errors import ApiError, api_error_handler

logger = logging.getLogger(__name__)


def get_app() -> FastAPI:
    # init
    app = FastAPI()

    # routes
    app.include_router(tg_parser_router)

    # middlewares
    app.middleware("http")(log_extra_middleware)

    # exception handlers
    app.add_exception_handler(exc_class_or_status_code=ApiError, handler=api_error_handler)

    # other

    return app
