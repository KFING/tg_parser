import os
from pathlib import Path

import yt_dlp


def _build_ydl_opts_for_video_subtitle() -> dict:
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
        "writeautomaticsub": True,
        "subtitlesformat": "srt",
        'cachedir': 'subtitles/',

    }
    return base

with yt_dlp.YoutubeDL(_build_ydl_opts_for_video_subtitle()) as ydl:
    a = ydl.download([f"https://www.youtube.com/watch?v=xVKx0Hjcvr8"])
