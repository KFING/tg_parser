from datetime import date, datetime, timezone

import yt_dlp
from pydantic import HttpUrl
from redis.asyncio import Redis

from src.common.async_utils import run_on_loop, sync_to_async
from src.dto import redis_models
from src.dto.feed_rec_info import Channel, MediaFormat, Post, RawPostMedia, Source, TaskStatus, MediaResolution, RawPostMediaExt

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)


rds = Redis(host="localhost", port=60379)


def _build_ydl_opts(**overrides) -> dict:
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
        "proxy": "http://localhost:10000"
    }
    base.update(overrides)
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


def _video_info_from_infodict(channel_name: str, data: dict) -> Post:
    post = Post(
        source=Source.YOUTUBE,
        channel_name=channel_name,
        title=data["fulltitle"],
        post_id=data["id"],
        description=data["description"],
        content=None,
        pb_date=_parse_upload_date(data["upload_date"]),
        link=HttpUrl(data["uploader_url"]),
        media=_audio_only_formats(data["formats"] or []),
    )
    print("geeeeet")
    return post


def get_channel_posts_info(channel_name: str) -> list[Post]:
    with yt_dlp.YoutubeDL(_build_ydl_opts()) as ydl:
        listing = ydl.extract_info(f"https://www.youtube.com/@mit", download=False)
        entries = listing["entries"] or []
        out: list[Post] = []
        for e in entries:
            try:
                out.append(_video_info_from_infodict(channel_name, e))

            except Exception:
                continue
        return out

posts = get_channel_posts_info("mit")

for post in posts:
    print(post.pb_date)
