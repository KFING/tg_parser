from datetime import datetime

from pydantic import BaseModel, HttpUrl


class TgPost(BaseModel):
    tg_channel_id: str
    tg_post_id: int
    content: str
    pb_date: datetime
    link: HttpUrl
