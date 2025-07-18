from datetime import datetime, timedelta
from enum import Enum, StrEnum, unique
from pathlib import Path

from pydantic import BaseModel, HttpUrl


@unique
class Source(Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"


@unique
class Lang(Enum):
    EN = "en"
    RU = "ru"


class MediaFormat(StrEnum):
    MP3 = "mp3"
    MP4 = "mp4"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    DOCX = "docx"
    TXT = "txt"
    PDF = "pdf"
    DOC = "doc"
    OTHER_FORMAT = "other_format"


class RawPostMedia(BaseModel):
    url: HttpUrl
    format: MediaFormat
    downloaded_file: Path | HttpUrl | None


class FeedRecPostCaption(BaseModel):
    lang: Lang
    raw: str
    parsed: list[tuple[timedelta, str]]


class FeedRecPostTimeLine(BaseModel):
    lang: Lang
    raw: str
    parsed: list[tuple[timedelta, str]]


class RawPostMediaExt(RawPostMedia):
    quality_raw: str | None  # for images is NONE
    preview: RawPostMedia | None
    captions: list[FeedRecPostCaption]
    timeline: list[FeedRecPostTimeLine]


class FeedRecPostShort(BaseModel, frozen=True, extra="forbid"):
    src: Source
    channel_id: str
    post_id: str

    url: HttpUrl
    title: str | None
    posted_at: datetime

    media: list[RawPostMediaExt]


class TmpListFeedRecPostShort(BaseModel):
    posts: list[FeedRecPostShort]


class TmpListMedia(BaseModel):
    media: list[RawPostMediaExt]


class FeedRecPostContent(BaseModel):
    lang: Lang
    content: str


class FeedRecPostFull(FeedRecPostShort, frozen=True, extra="forbid"):
    contents: list[FeedRecPostContent]
