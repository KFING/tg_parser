from __future__ import annotations
from datetime import datetime, timezone, date
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from pydantic import HttpUrl

import yt_dlp

from src.common.async_utils import sync_to_async, run_on_loop
from src.dto import redis_models
from src.dto.feed_rec_info import Source, TaskStatus, Post, Channel, RawPostMedia, MediaFormat
from redis.asyncio import Redis

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)


rds = Redis(host="redis", port=6379)



def _build_ydl_opts(**overrides) -> dict:
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
    }
    base.update(overrides)
    return base


def _parse_upload_date(s: Optional[str]) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y%m%data")
    except ValueError:
        return None


def _audio_only_formats(formats: List[dict]) -> RawPostMedia | None:
    for f in formats or []:
        if f.get("audio_ext") == 'webm' and f.get("url"):
            return RawPostMedia(
                format=MediaFormat.WEBM,
                url=HttpUrl(f["url"]),
                downloaded_file=None,
            )


def _video_info_from_infodict(channel_name: str, data: dict) -> Post:
    return Post(
        post_id=data.get("id"),
        link=HttpUrl(data.get("webpage_url") or data.get("original_url") or ""),
        title=data.get("title"),
        channel_name=channel_name,
        content=data.get("description"),
        pb_date=_parse_upload_date(data.get("upload_date")),
        media=_audio_only_formats(data.get("formats") or []),
    )


@sync_to_async
def get_channel_info(channel_url: str) -> Channel:
    with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None))) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        title = info.get("title") or info.get("channel") or info.get("uploader")
        description = info.get("description")

        if not description:
            try:
                about = ydl.extract_info(channel_url.rstrip("/") + "/about", download=False)
                description = about.get("description") or description
                if not title:
                    title = about.get("title")
            except Exception:
                pass

        return Channel(
            source=Source.YOUTUBE,
            link=HttpUrl(info.get("channel_name") or channel_url),
            channel_id=info.get("channel_id") or info.get("uploader_id"),
            channel_name=info.get("channel") or None,   # не всегда присутствует как @handle
            description=description,
        )


@sync_to_async
def iter_channel_video_ids(channel_name: str) -> List[str]:

    with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None), extract_flat=True)) as ydl:
        listing = ydl.extract_info(f'https://www.youtube.com/@{channel_name}', download=False)
        entries = listing.get("entries") or []
        ids = []
        for e in entries:
            if e.get("ie_key") == "Youtube" and e.get("id"):
                ids.append(e["id"])
            elif e.get("url") and "watch?v=" in e["url"]:
                ids.append(e["url"].split("watch?v=")[-1].split("&")[0])
        return ids


@sync_to_async
def get_all_videos(channel_name: str) -> List[Post]:

    video_ids = run_on_loop(iter_channel_video_ids(channel_name))
    out: List[Post] = []

    with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None))) as ydl:
        for vid in video_ids:
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                info = ydl.extract_info(url, download=False)
                out.append(_video_info_from_infodict(channel_name, info))
            except Exception:
                continue
    return out


async def get_channel_posts_list(
    channel_name: str, *, log_extra: dict[str, str]
) -> list[Post] | None:

    dt_to = await rds.get(redis_models.source_channel_name_dt_to(Source.TELEGRAM, channel_name))
    if not dt_to:
        await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
        return None
    dt_from = await rds.get(redis_models.source_channel_name_dt_from(Source.TELEGRAM, channel_name))
    if not dt_from:
        await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
        return None

    utc_dt_to = datetime.fromisoformat(dt_to.decode("utf-8"))
    utc_dt_from = datetime.fromisoformat(dt_from.decode("utf-8"))

    all_videos = await get_all_videos(channel_name)
    in_range: List[Post] = []
    for video in all_videos:
        if not video.upload_date:
            continue
        if utc_dt_from <= video.upload_date <= utc_dt_to:
            in_range.append(video)

    in_range.sort(key=lambda v: v.upload_date or date.min, reverse=True)
    return in_range
