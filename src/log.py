import contextlib
import logging
import time
import warnings
from collections.abc import Iterator
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Final

import sentry_sdk
from pythonjsonlogger import jsonlogger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from src.env import ROOT_PATH, AppName, LogLevel, settings
from srv.common.const import FG

logger: Final = logging.getLogger(__name__)


class EndpointFilter(logging.Filter):
    def __init__(
        self,
        path: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1


warnings.simplefilter(action="ignore", category=FutureWarning)
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("databases").setLevel(logging.ERROR)
logging.getLogger("sentry").setLevel(logging.ERROR)
logging.getLogger("sentry_sdk").setLevel(logging.ERROR)
logging.getLogger("sentry_sdk.errors").setLevel(logging.ERROR)
logging.getLogger("py.warnings").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)


_LVL_COLOR_MAP = {
    logging.WARNING: FG.DARK_yellow,
    logging.INFO: FG.LightGray,
    logging.DEBUG: FG.LightGray,
    logging.CRITICAL: FG.Red,
    logging.ERROR: FG.Red,
    logging.FATAL: FG.Red,
    logging.NOTSET: FG.Default,
}


_LVL_NAME_MAP = {
    logging.WARNING: "W",
    logging.INFO: "I",
    logging.DEBUG: "D",
    logging.CRITICAL: "E",
    logging.ERROR: "E",
    logging.FATAL: "E",
    logging.NOTSET: " ",
}


STARTED_AT = datetime.now()
_log_def_keys = {
    "name",
    "msg",
    "asctime",
    "args",
    "levelname",
    "levelno",
    "color_message",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "req_id",
    "req_status",
    "req_duration",
}


class ExFormatter(logging.Formatter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__("%(asctime)s", "%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        try:
            dt = datetime.strptime(super().format(record), "%Y-%m-%d %H:%M:%S")
            at = str(int((max(STARTED_AT, dt) - STARTED_AT).total_seconds() * 10))
        except Exception:
            at = "N/A"

        req_data = record.__dict__
        extra = {k: v for k, v in req_data.items() if k not in _log_def_keys}
        req_id = req_data.get("req_id", "")
        try:
            req_status = int(req_data.get("req_status", "-22"))
        except Exception:
            req_status = -33
        try:
            req_duration = float(req_data.get("req_duration", "0.0"))
        except Exception:
            req_duration = 0.0
        req_started: bool = req_status == -1
        req_ended: bool = req_status >= 0

        req_mark = "    |"
        if req_id:
            req_mark = f"{str(req_id)[-9:]:0>9}|"
        elif record.name not in {"src.app_api.lifecycle_events", "src.log"}:
            req_mark = f"{FG.Red}NO_REQ_ID{_LVL_COLOR_MAP[record.levelno]}|"

        status_code_fmt = f"{FG.Red}{req_status}{FG.Default}"
        if 0 < req_status < 400:
            status_code_fmt = f"{FG.Green}{req_status}{FG.Default}"
        elif 400 <= req_status < 500:
            status_code_fmt = f"{FG.DARK_yellow}{req_status}{FG.Default}"

        rec_name = f"{record.name}:{record.levelno}"
        if record.name.startswith("src."):
            rec_name = f'./{"/".join(record.name.split("."))}.py:{record.levelno}'
        elif record.name == "__main__":
            import __main__

            rec_name = f"{Path(__main__.__file__).relative_to(ROOT_PATH)}:{record.levelno}"

        extra_fmt = f" :: {extra}" if len(extra) > 0 else ""
        ln_start = "\n\n" if req_started else ""
        ln_end = f" === {status_code_fmt}" f" {FG.Cyan if req_duration <= 0.2 else FG.DARK_red}({req_duration:0.2f}s){FG.Default}" f"\n\n" if req_ended else ""
        return (
            f"{ln_start}{_LVL_COLOR_MAP[record.levelno]}{_LVL_NAME_MAP[record.levelno]} {at[-5:]:0>5}"
            f"|{req_mark} {rec_name} |{FG.Default} {record.message}{extra_fmt}{ln_end}"
        )


format = "%(asctime)s %(levelname)s %(name)s %(module)s:%(lineno)s %(message)s"
json_formatter = jsonlogger.JsonFormatter(format)  # type: ignore
local_text_formatter = ExFormatter()
_logger_was_initialized = False


def setup_logging(log_lvl: LogLevel = settings.LOG_LVL) -> None:
    global _logger_was_initialized  # noqa: PLW0603
    if _logger_was_initialized:
        return
    _logger_was_initialized = True

    logHandler = logging.StreamHandler()

    if settings.is_testing or settings.is_local:
        logHandler.setFormatter(local_text_formatter)
        logging.basicConfig(level=logging.INFO, format="%(asctime)s", handlers=[logHandler])
        logging.getLogger("src").setLevel(logging.DEBUG)
    else:
        logHandler.setFormatter(json_formatter)
        logging.basicConfig(level=logging.WARNING, format=format, handlers=[logHandler])
        logging.getLogger("src").setLevel(getattr(logging, log_lvl.value))

    logging.getLogger("databases").setLevel(logging.ERROR)
    logging.getLogger("sentry").setLevel(logging.ERROR)
    logging.getLogger("sentry_sdk").setLevel(logging.ERROR)
    logging.getLogger("sentry_sdk.errors").setLevel(logging.ERROR)
    logging.getLogger("py.warnings").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)


@contextlib.contextmanager
def scope(logger: logging.Logger, msg: str, *, req_id: str | None = None, enable_endings: bool = True) -> Iterator[dict[str, str]]:  # noqa: C901
    setup_logging()
    setup_sentry()
    if settings.is_testing:
        req_id = ""
    elif settings.is_local or not req_id:
        req_id = f"{int(time.monotonic() * 1000).to_bytes(8, byteorder='big').hex():0>16}"
    log_extra = {"req_id": req_id}
    if enable_endings:
        logger.debug(msg, extra={**log_extra, "req_status": -1})
    started_at = time.monotonic()
    try:
        yield log_extra
        if "req_status" not in log_extra:
            log_extra["req_status"] = "200"
    except Exception as e:
        logger.exception(e, exc_info=e, extra={**log_extra, "req_status": -1})
        sentry_sdk.capture_exception(e)
        log_extra["req_status"] = "500"
        raise
    finally:
        log_extra["req_duration"] = f"{time.time() - started_at:0.5f}"
        try:
            status = int(str(log_extra.get("req_status", "-1") or "-2"))
        except Exception:
            status = -3
        log_extra["req_status"] = str(status)

        if enable_endings:
            if status <= 0:
                logger.warning(msg, extra=log_extra)
            elif status < 400:
                logger.info(msg, extra=log_extra)
            elif status < 500:
                logger.warning(msg, extra=log_extra)
            else:
                logger.error(msg, extra=log_extra)


class SentryScope(Enum):
    APP_API = "APP_API"
    APP_CELERY = "APP_CELERY"
    OTHER = "OTHER"


_sentry_was_intialized = False


def setup_sentry() -> None:
    global _sentry_was_intialized  # noqa: PLW0603
    if _sentry_was_intialized:
        return
    _sentry_was_intialized = True

    dsn = settings.SENTRY_DSN

    if settings.app == AppName.app_api:
        sentry_scope = SentryScope.APP_API
    elif settings.app == AppName.app_celery:
        sentry_scope = SentryScope.APP_CELERY
    else:
        sentry_scope = SentryScope.OTHER

    integrations = []
    match sentry_scope:
        case SentryScope.APP_API:
            integrations = [
                StarletteIntegration(transaction_style="endpoint", failed_request_status_codes=[range(403, 599)]),
                FastApiIntegration(transaction_style="endpoint", failed_request_status_codes=[range(403, 599)]),
                CeleryIntegration(monitor_beat_tasks=True),
            ]
        case SentryScope.APP_CELERY:
            integrations = [
                CeleryIntegration(monitor_beat_tasks=True),
            ]
        case SentryScope.OTHER:
            integrations = []

    if not dsn:
        logger.warning("Sentry NOT initialized - empty DSN")
        return

    sentry_logging = LoggingIntegration(level=logging.DEBUG, event_level=logging.CRITICAL)
    sentry_sdk.init(
        dsn=str(dsn),
        enable_tracing=False,
        debug=not settings.is_prod,
        max_breadcrumbs=50,
        environment=settings.ENV.value,
        integrations=[
            *integrations,
            sentry_logging,
            AsyncioIntegration(),
        ],
        # release=CONTAINER_STAMP,
        **({} if not settings.SENTRY_CA_BUNDLE else {"ca_certs": str(settings.SENTRY_CA_BUNDLE)}),  # type: ignore
    )
    sentry_sdk.set_tag("app_name", settings.app.value)
    sentry_sdk.set_context("application", {"name": settings.app.value})
    sentry_sdk.set_level("error")
    logger.info("Sentry initialized")
