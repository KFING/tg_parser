from datetime import datetime

from pydantic import BaseModel

from src.dto.feed_rec_info import Lang

class ParsingParametersApiMdl(BaseModel):
    channel_name: str
    dt_to: datetime
    dt_from: datetime

