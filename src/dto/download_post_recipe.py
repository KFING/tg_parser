from enum import StrEnum, unique

from pydantic import BaseModel

from src.dto.feed_rec_info import Lang


@unique
class DownloadQuality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    BEST = "best"


class DownloadPostContentRecipe(BaseModel, frozen=True):
    content: bool
    captions: bool
    timeline: bool

    download_preview_image: bool
    download_document: bool
    download_video_quality: DownloadQuality | None
    download_audio_quality: DownloadQuality | None
    download_image_quality: DownloadQuality | None

    lang: Lang
