from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse



class AppError(Exception):
    api_code: int = 500


class ScrapperError(AppError):
    api_code: int = 500


class NotFoundChannelScrapperError(ScrapperError):
    api_code: int = 404
    channel_id: str

    def __init__(self, channel_id: str) -> None:
        super().__init__(f'Channel "{channel_id}" not found in {self.src}')
        self.channel_id = channel_id


class NotFoundPostScrapperError(ScrapperError):
    api_code: int = 404
    post_id: str

    def __init__(self, post_id: str) -> None:
        super().__init__(f'Post "{post_id}" not found in {self.src}')
        self.post_id = post_id


class ApiError(AppError):
    error_type: str
    error_message: str
    error_details: str = ""
    http_status_code: int = 500
    errors: list[dict[str, str]] | None = None


def api_error_handler(_request: Request, ex: Exception) -> JSONResponse:
    assert isinstance(ex, ApiError)
    error_content = {"error_type": ex.error_type, "error_message": ex.error_message, "error_details": ex.error_details, "errors": ex.errors or []}
    return JSONResponse(error_content, status_code=ex.http_status_code)


class ApiResponseError(ApiError):
    http_status_code: int = 500


class ScrapperConnectionError(ApiError):
    http_status_code: int = 403


class PermissionDeniedError(ApiError):
    http_status_code: int = 403


class NotFoundFileError(ApiResponseError):
    channel_id: str
    post_id: str
    http_status_code: int = 404

    def __init__(self, channel_id: str, post_id: str) -> None:
        super().__init__(f'Post "{post_id}" not found in {channel_id}/{post_id}')
        self.channel_id = channel_id
        self.post_id = post_id


class JSONDecoderError(ApiResponseError):
    channel_id: str
    post_id: str
    http_status_code: int = 422

    def __init__(self, channel_id: str, post_id: str) -> None:
        super().__init__(f'Post "{post_id}" failed parsed json to FeedRecPostFull in {channel_id}/{post_id}')
        self.channel_id = channel_id
        self.post_id = post_id


def fmt_err(err: Exception | str | None, tb: Any = None) -> str:
    if isinstance(err, Exception):
        tb = f"\n\n{tb}" if tb else ""
        return f"{type(err).__name__}: {err}{tb}".strip()
    if err is None:
        return ""
    return err.strip()
