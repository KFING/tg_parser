import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from src.app_api.auth.auth import AccessBearerToken, AuthUser, get_auth
from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models.feed_rec_request_info import RequestRecipe
from src.app_api.models.response_models.feed_rec_response_info import FeedRecResponsePostFull, FeedRecResponsePostsList
from src.dto.feed_rec_info import FeedRecPostFull, Lang, Source, TmpListFeedRecPostShort
from src.env import SCRAPPER_RESULTS_DIR
from src.errors import ApiError, JSONDecoderError, NotFoundFileError
from src.service_keycloak.keycloak_open_id import keycloak_openid

logger = logging.getLogger(__name__)


source_post_router = APIRouter(
    tags=["scrapper info"],
)


class YoutubeNotFoundFileError(NotFoundFileError):
    error_type = "youtube_not_found_error"
    error_message = "requested post or channel does not exist"
    http_status_code = 404
    src = Source.YOUTUBE


class YoutubeJSONDecoderError(JSONDecoderError):
    error_type = "youtube_invalid_content_error"
    error_message = "response JSON error"
    http_status_code = 500
    src = Source.YOUTUBE


class FailedAuthenticationError(ApiError):
    error_type = "failed_authentication_error"
    error_message = "invalid username or password"
    http_status_code = 401


def get_post_data(
    source: Source, channel_id: str, post_id: str, recipe: RequestRecipe, *, auth_user: AuthUser = Depends(get_auth), log_extra: dict[str, str]
) -> FeedRecResponsePostFull:
    if not (SCRAPPER_RESULTS_DIR / source.value / channel_id / post_id / f"{post_id}.json").exists():
        raise YoutubeNotFoundFileError(channel_id, post_id)
    try:
        with (SCRAPPER_RESULTS_DIR / Source.YOUTUBE.value / channel_id / post_id / f"{post_id}.json").open("r", encoding="utf-8") as f:
            data = FeedRecPostFull(**json.load(f))
        return FeedRecResponsePostFull(data=data)
    except HTTPException as e:
        logger.error(f"get_data({post_id}) -> failed parse json to FeedRecPostFull :: {post_id}", e, extra=log_extra)
        raise YoutubeJSONDecoderError(channel_id, post_id) from e


def get_channel_data(source: Source, channel_id: str, *, auth_user: AuthUser = Depends(get_auth), log_extra: dict[str, str]) -> FeedRecResponsePostsList:
    if not (SCRAPPER_RESULTS_DIR / source.value / channel_id / f"{channel_id}.json").exists():
        raise YoutubeNotFoundFileError(channel_id, "")
    try:
        with (SCRAPPER_RESULTS_DIR / Source.YOUTUBE.value / channel_id / f"{channel_id}.json").open("r", encoding="utf-8") as f:
            data = TmpListFeedRecPostShort(**json.load(f))
        return FeedRecResponsePostsList(data=data)
    except HTTPException as e:
        logger.error(f"get_data({channel_id}) -> failed parse json to FeedRecPostFull :: {channel_id}", e, extra=log_extra)
        raise YoutubeJSONDecoderError(channel_id, "") from e


def get_playlist_data(source: Source, playlist_id: str, *, auth_user: AuthUser = Depends(get_auth), log_extra: dict[str, str]) -> FeedRecResponsePostsList:
    if not (SCRAPPER_RESULTS_DIR / source.value / playlist_id / f"{playlist_id}.json").exists():
        raise YoutubeNotFoundFileError(playlist_id, "")
    try:
        with (SCRAPPER_RESULTS_DIR / Source.YOUTUBE.value / playlist_id / f"{playlist_id}.json").open("r", encoding="utf-8") as f:
            data = TmpListFeedRecPostShort(**json.load(f))
        return FeedRecResponsePostsList(data=data)
    except HTTPException as e:
        logger.error(f"get_data({playlist_id}) -> failed parse json to FeedRecPostFull :: {playlist_id}", e, extra=log_extra)
        raise YoutubeJSONDecoderError(playlist_id, "") from e


@source_post_router.get("/sources/{source}/channels/{channel_id}/posts/{post_id}")
async def api_route_get_youtube_post(
    source: Source, channel_id: str, post_id: str, *, auth_user: AuthUser = Depends(get_auth), log_extra: dict[str, str] = Depends(get_log_extra)
) -> FeedRecResponsePostFull:
    return get_post_data(source, channel_id, post_id, RequestRecipe(lang=Lang.EN, content=True, captions=True, timeline=True, media=True), log_extra=log_extra)


@source_post_router.get("/sources/{source}/channels/{channel_id}")
async def api_route_get_youtube_channel_posts(
    source: Source, channel_id: str, *, auth_user: AuthUser = Depends(get_auth), log_extra: dict[str, str] = Depends(get_log_extra)
) -> FeedRecResponsePostsList:
    return get_channel_data(source, channel_id, log_extra=log_extra)


@source_post_router.get("/sources/{source}/playlists/{playlist_id}")
async def api_route_get_youtube_playlist_posts(
    source: Source, playlist_id: str, *, auth_user: AuthUser = Depends(get_auth), log_extra: dict[str, str] = Depends(get_log_extra)
) -> FeedRecResponsePostsList:
    return get_playlist_data(source, playlist_id, log_extra=log_extra)


@source_post_router.post("/swagger-auth", include_in_schema=False)
async def api_route_get_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> AccessBearerToken:
    try:
        token = await keycloak_openid.a_token(form_data.username, form_data.password)
    except HTTPException as e:
        raise FailedAuthenticationError from e
    return AccessBearerToken(access_token=token["access_token"], type_token="bearer")


# user: User = Depends(get_auth_user("policy_name"))
# def save_to_disk(info: FeedRecPostFull) -> FeedRecResponseInfo:
#     (SCRAPPER_RESULTS_DIR / info.src.value / info.channel_id / info.post_id).mkdir(exist_ok=True, parents=True)
#     (SCRAPPER_RESULTS_DIR / info.src.value / info.channel_id / info.post_id / f"{info.post_id}.json").write_text(info.model_dump_json(indent=4))
#     return FeedRecResponseInfo(data=info)
#
#
# @source_post_router.post("/post/{post_id}/")
# async def download_youtube_post(recipe: RequestRecipe, log_extra: dict[str, str]) -> FeedRecResponseInfo:
#     post = await youtube_scrapy.download_post(post_id=recipe.post_id, recipe=recipe, log_extra=log_extra)
#     if isinstance(post, FeedRecPostFull):
#         return save_to_disk(post)
