from __future__ import annotations
import datetime as dt
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

import yt_dlp


# ---------- Модели данных ----------

@dataclass
class ChannelInfo:
    url: str
    channel_id: Optional[str]
    handle: Optional[str]
    title: Optional[str]
    description: Optional[str]


@dataclass
class AudioFormat:
    format_id: str
    ext: Optional[str]
    acodec: Optional[str]
    abr: Optional[float]  # kbps
    url: str


@dataclass
class VideoInfo:
    id: str
    url: str
    title: Optional[str]
    description: Optional[str]
    upload_date: Optional[dt.date]
    audio_formats: List[AudioFormat]
    subtitles: Dict[str, List[Dict[str, Any]]]           # {lang: [ {url, ext, ...}, ... ]}
    automatic_captions: Dict[str, List[Dict[str, Any]]]  # {lang: [ {url, ext, ...}, ... ]}


# ---------- Вспомогательные утилиты ----------

def _build_ydl_opts(**overrides) -> dict:
    """
    Базовые опции для извлечения МЕТАДАННЫХ (без скачивания контента).
    """
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,  # для видео нужны полноразмерные метаданные с formats/subtitles
        "ignoreerrors": True,   # пропускать проблемные элементы
        # При необходимости можно добавить cookies / auth для age-restricted:
        # "cookiefile": "cookies.txt",
    }
    base.update(overrides)
    return base


def _parse_upload_date(s: Optional[str]) -> Optional[dt.date]:
    if not s:
        return None
    # yt-dlp отдаёт YYYYMMDD
    try:
        return dt.datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


def _audio_only_formats(formats: List[dict]) -> List[AudioFormat]:
    out: List[AudioFormat] = []
    for f in formats or []:
        # audio-only: у таких форматов vcodec == 'none'
        if f.get("vcodec") == "none" and f.get("url"):
            out.append(AudioFormat(
                format_id=str(f.get("format_id")),
                ext=f.get("ext"),
                acodec=f.get("acodec"),
                abr=(float(f["abr"]) if f.get("abr") is not None else None),
                url=f["url"],
            ))
    # По убыванию битрейта, чтобы «лучшие» были первыми
    out.sort(key=lambda x: (x.abr or 0.0), reverse=True)
    return out


def _video_info_from_infodict(d: dict) -> VideoInfo:
    return VideoInfo(
        id=d.get("id"),
        url=d.get("webpage_url") or d.get("original_url") or "",
        title=d.get("title"),
        description=d.get("description"),
        upload_date=_parse_upload_date(d.get("upload_date")),
        audio_formats=_audio_only_formats(d.get("formats") or []),
        subtitles=d.get("subtitles") or {},
        automatic_captions=d.get("automatic_captions") or {},
    )


# ---------- Публичные функции ----------

def get_channel_info(channel_url: str) -> ChannelInfo:
    """
    Возвращает title/description канала + несколько полезных идентификаторов.
    """
    with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None))) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        # yt-dlp для каналов обычно возвращает «плейлист»-объект вкладки /videos
        title = info.get("title") or info.get("channel") or info.get("uploader")
        description = info.get("description")

        # Если описания нет, пробуем вкладку /about (бывает надёжнее для description)
        if not description:
            try:
                about = ydl.extract_info(channel_url.rstrip("/") + "/about", download=False)
                description = about.get("description") or description
                # На всякий — заголовок
                if not title:
                    title = about.get("title")
            except Exception:
                pass

        return ChannelInfo(
            url=info.get("channel_url") or channel_url,
            channel_id=info.get("channel_id") or info.get("uploader_id"),
            handle=info.get("channel") or None,   # не всегда присутствует как @handle
            title=title,
            description=description,
        )


def iter_channel_video_ids(channel_url: str) -> List[str]:
    """
    Быстрый список id всех видео канала без тяжёлых запросов форматов.
    Затем по каждому id можно сделать подробный extract_info.
    """
    # Здесь используем extract_flat=True, чтобы получить только «карточки»
    with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None), extract_flat=True)) as ydl:
        listing = ydl.extract_info(channel_url, download=False)
        entries = listing.get("entries") or []
        ids = []
        for e in entries:
            # e может быть {id, url, title, ...}, иногда вложенные плейлисты — пропустим
            if e.get("ie_key") == "Youtube" and e.get("id"):
                ids.append(e["id"])
            elif e.get("url") and "watch?v=" in e["url"]:
                # как запасной вариант достанем id из URL
                ids.append(e["url"].split("watch?v=")[-1].split("&")[0])
        return ids


def get_all_videos(channel_url: str) -> List[VideoInfo]:
    """
    Полные метаданные по всем видео канала.
    ВНИМАНИЕ: для крупных каналов это может быть заметно долго (делается по одному запросу на видео).
    """
    video_ids = iter_channel_video_ids(channel_url)
    out: List[VideoInfo] = []

    with yt_dlp.YoutubeDL(_build_ydl_opts(cookiesfrombrowser=("firefox", None, None, None))) as ydl:
        for vid in video_ids:
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                info = ydl.extract_info(url, download=False)
                out.append(_video_info_from_infodict(info))
            except Exception:
                # игнорируем битые / недоступные элементы
                continue
    return out


def get_videos_by_date(
    channel_url: str,
    date_from: dt.date,
    date_to: dt.date,
) -> List[VideoInfo]:
    """
    Возвращает видео, опубликованные в [date_from; date_to] (включительно).
    """
    all_videos = get_all_videos(channel_url)
    in_range: List[VideoInfo] = []
    for v in all_videos:
        if not v.upload_date:
            continue
        if date_from <= v.upload_date <= date_to:
            in_range.append(v)
    # По дате (новые сверху)
    in_range.sort(key=lambda v: v.upload_date or dt.date.min, reverse=True)
    return in_range


"""# ---------- Пример использования ----------
if __name__ == "__main__":
    CHANNEL = "https://www.youtube.com/@jp-f6s"  # подставьте свой URL

    info = get_channel_info(CHANNEL)
    print("CHANNEL:", asdict(info))

    videos = get_all_videos(CHANNEL)
    print(f"TOTAL VIDEOS: {len(videos)}")
    if videos:
        print("SAMPLE VIDEO:", asdict(videos[0]))

    # Диапазон дат
    start = dt.date(2025, 7, 10)
    end = dt.date(2025, 7, 14)
    ranged = get_videos_by_date(CHANNEL, start, end)
    print(f"IN RANGE [{start}..{end}]: {len(ranged)}")"""
