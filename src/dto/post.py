from datetime import datetime
from enum import unique, Enum

from pydantic import BaseModel, HttpUrl

from src.dto.feed_rec_info import RawPostMediaExt


class Post(BaseModel):
    channel_id: int
    post_id: str
    content: str
    pb_date: datetime
    link: HttpUrl
    media: list[RawPostMediaExt] | None

@unique
class Source(Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
