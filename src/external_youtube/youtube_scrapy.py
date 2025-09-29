from __future__ import annotations

import logging
from datetime import date, datetime, timezone

import yt_dlp
from pydantic import HttpUrl
from redis.asyncio import Redis

from src.common.async_utils import run_on_loop, sync_to_async
from src.dto import redis_models
from src.dto.feed_rec_info import Channel, MediaFormat, Post, RawPostMedia, Source, TaskStatus, MediaResolution, RawPostMediaExt

logger = logging.getLogger(__name__)


START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)


rds = Redis(host="localhost", port=60379)

def _build_ydl_opts_for_video_subtitle() -> dict:
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
        "subtitlesformat": "srt",
        "writeautomaticsub": True,
    }
    return base

def _build_ydl_opts_for_videos() -> dict:
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
    }
    return base


def _parse_upload_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _audio_only_formats(formats: list[dict]) -> RawPostMediaExt | None:

    for f in formats:
        if f["resolution"] != MediaResolution.AUDIO_ONLY.value:
            continue
        if f["audio_ext"] == MediaFormat.WEBM.value and f["url"]:

            preview = RawPostMedia(
                url=HttpUrl(f["url"]),
                resolution=MediaResolution.AUDIO_ONLY,
                audio_ext=MediaFormat.WEBM,
                downloaded_file=None,
            )
            return RawPostMediaExt(
                preview=preview,
                transcription=[]
            )


def _video_info_from_info_dict(channel_name: str, data: dict) -> Post:
    post_id = data["id"]
    with yt_dlp.YoutubeDL(_build_ydl_opts_for_video_subtitle()) as ydl:
        ydl.download(f"https://www.youtube.com/watch?v={post_id}")
    post = Post(
        source=Source.YOUTUBE,
        channel_name=channel_name,
        title=data["fulltitle"],
        post_id=post_id,
        description=data["description"],
        content=None,
        pb_date=_parse_upload_date(data["upload_date"]),
        link=HttpUrl(data["uploader_url"]),
        media=_audio_only_formats(data["formats"] or []),
    )
    print("geeeeet")
    return post


@sync_to_async
def get_channel_info(channel_url: str) -> Channel:
    with yt_dlp.YoutubeDL(_build_ydl_opts()) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        title = info["title"] or info["channel"] or info["uploader"]
        description = info["description"]

        if not description:
            try:
                about = ydl.extract_info(channel_url.rstrip("/") + "/about", download=False)
                description = about["description"] or description
                if not title:
                    title = about["title"]
            except Exception:
                pass

        return Channel(
            source=Source.YOUTUBE,
            link=HttpUrl(info["channel_name"] or channel_url),
            channel_id=info["channel_id"] or info["uploader_id"],
            channel_name=info["channel"] or None,  # не всегда присутствует как @handle
            description=description,
        )


@sync_to_async
def get_channel_posts_info(channel_name: str) -> list[Post]:
    with yt_dlp.YoutubeDL(_build_ydl_opts_for_videos()) as ydl:
        listing = ydl.extract_info(f"https://www.youtube.com/@{channel_name}", download=False)
        entries = listing["entries"] or []
        out: list[Post] = []
        for e in entries:
            try:
                out.append(_video_info_from_info_dict(channel_name, e))

            except Exception:
                continue
        return out


"""@sync_to_async
def get_all_videos(channel_name: str) -> list[Post]:
    video_ids = run_on_loop(iter_channel_video_ids(channel_name))
    out: list[Post] = []
    print(f"Found {len(video_ids)} videos")
    with yt_dlp.YoutubeDL(_build_ydl_opts()) as ydl:
        for vid in video_ids:
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                info = ydl.extract_info(url, download=False)
                out.append(_video_info_from_infodict(channel_name, info))
            except Exception:
                continue
    return out"""


async def get_channel_posts_list(channel_name: str, *, log_extra: dict[str, str]) -> list[Post] | None:
    """dt_to = await rds.get(redis_models.source_channel_name_dt_to(Source.YOUTUBE, channel_name))
    if not dt_to:
        dt_to = END_OF_EPOCH
    dt_from = await rds.get(redis_models.source_channel_name_dt_from(Source.YOUTUBE, channel_name))
    if not dt_from:
        dt_from = START_OF_EPOCH
    utc_dt_to = datetime.fromisoformat(dt_to.decode("utf-8"))
    utc_dt_from = datetime.fromisoformat(dt_from.decode("utf-8"))"""
    logger.debug("get_channel_posts_list :: start to finding yt posts", extra=log_extra)
    all_videos = await get_channel_posts_info(channel_name)
    logger.debug(f"get_channel_posts_list :: found {len(all_videos)} videos", extra=log_extra)
    logger.debug(f"get_channel_posts_list :: found in_range {len(in_range)} videos", extra=log_extra)
    in_range.sort(key=lambda v: v.pb_date or date.min, reverse=True)
    logger.debug("get_channel_posts_list :: finish finding posts --> start to download subtitles", extra=log_extra)
    return in_range
