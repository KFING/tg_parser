from datetime import datetime

from pydantic import BaseModel, HttpUrl

from src.dto.feed_rec_info import RawPostMediaExt


class Post(BaseModel):
    channel_name: str
    post_id: int
    content: str
    pb_date: datetime
    link: HttpUrl
    media: list[RawPostMediaExt] | None
