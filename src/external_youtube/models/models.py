"""from enum import Enum

from pydantic import BaseModel, HttpUrl

class VideoExt(Enum):
    webm = "webm"

class AudioExt(Enum):
    webm = 'webm'
    mp4 = 'mp4'

class Format(BaseModel):
    format_id: str
    audio_ext: AudioExt
    video_ext: VideoExt
    url: HttpUrl

class Post(BaseModel):
    id: str
    channel_name: str
    full_title: str
    description: str
    formats: list[Format]

class Channel(BaseModel):
    id: str
    channel: str
    title: str
    description: str
    uploader_id: str
    entries: list[Post]"""
