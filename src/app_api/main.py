import logging

from fastapi import FastAPI

from src.app_api.middlewares import log_extra_middleware
from src.app_api.routes.auth_router import auth_router
from src.app_api.routes.paddle_router import paddle_router
from src.app_api.routes.sandbox_router import sandbox_router
from src.app_api.routes.source_post_router import source_post_router
from src.errors import ApiError, api_error_handler

logger = logging.getLogger(__name__)


def get_app() -> FastAPI:
    # init
    app = FastAPI()

    # routes
    app.include_router(sandbox_router)
    app.include_router(paddle_router)
    app.include_router(auth_router)
    app.include_router(source_post_router)

    # middlewares
    app.middleware("http")(log_extra_middleware)

    # exception handlers
    app.add_exception_handler(exc_class_or_status_code=ApiError, handler=api_error_handler)

    # other

    return app
