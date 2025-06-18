import asyncio
import logging
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from src import log
from src.env import settings

lock = asyncio.Lock()
logger = logging.getLogger(__name__)


async def get_log_extra(request: Request) -> dict[str, str]:
    return getattr(request.state, "log_extra", {})


async def log_extra_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    if settings.is_local:
        await lock.acquire()
    host: str = request.headers.get("x-forwarded-for", f"~{getattr(request.client, 'host', 'unknown')}:{getattr(request.client, 'port', 'unknown')}")
    req_id = request.headers.get("x-correlation-id") or request.headers.get("x-operation-id") or request.headers.get("x-request-id")
    with log.scope(
        logger,
        f"{request.method} {request.url.path} {request.url.query} from {host}",
        req_id=req_id,
        enable_endings=request.url.path != "/health",
    ) as log_extra:
        request.state.req_id = log_extra["req_id"]
        request.state.log_extra = log_extra
        response = await call_next(request)
        log_extra["req_status"] = str(response.status_code)
        # if CONTAINER_STAMP:
        #    response.headers["X-Stoic-Backend-Version"] = CONTAINER_STAMP
        response.headers["X-Request-ID"] = request.headers.get("x-request-id", log_extra["req_id"])
        response.headers["X-Operation-ID"] = log_extra["req_id"]
        response.headers["X-Correlation-ID"] = log_extra["req_id"]
    if settings.is_local:
        lock.release()
    return response
