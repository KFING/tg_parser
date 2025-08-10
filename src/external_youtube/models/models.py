from enum import Enum

from pydantic import BaseModel, HttpUrl

class VideoExt(Enum):
    webm = "webm"

class AudioExt(Enum):
    webm = 'webm'
    mp4 = 'mp4'

class YtFormat(BaseModel):
    format_id: str
    audio_ext: AudioExt
    video_ext: VideoExt
    url: HttpUrl
    manifest_url: HttpUrl

class Entry(BaseModel):
    id: str
    channel_id: str
    full_title: str
    description: str
    age_limit: int
    live_status: str
    formats: list[YtFormat]

class Channel(BaseModel):
    id: str
    channel: str
    title: str
    description: str
    uploader_id: str
    entries: list[Entry]
