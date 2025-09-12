from datetime import datetime

from pydantic import BaseModel

from src.dto.feed_rec_info import Source


class ParsingParametersApiMdl(BaseModel):
    source: Source
    channel_name: str
    dt_to: datetime
    dt_from: datetime


class InfoParsingParametersApiMdl(BaseModel):
    source: Source
    channel_name: str
