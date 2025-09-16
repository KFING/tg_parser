from __future__ import annotations

from datetime import date, datetime, timezone

import yt_dlp
from pydantic import HttpUrl
from redis.asyncio import Redis

from src.common.async_utils import run_on_loop, sync_to_async
from src.dto import redis_models
from src.dto.feed_rec_info import Channel, MediaFormat, Post, RawPostMedia, Source, TaskStatus

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

with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None), extract_flat=True)) as ydl:
    listing = ydl.extract_info(f"https://www.youtube.com/@mozgoprav_official", download=False)
    entries = listing.get("entries") or []
    ids = []
    for e in entries:
        if e.get("ie_key") == "Youtube" and e.get("id"):
            ids.append(e["id"])
        elif e.get("url") and "watch?v=" in e["url"]:
            ids.append(e["url"].split("watch?v=")[-1].split("&")[0])
