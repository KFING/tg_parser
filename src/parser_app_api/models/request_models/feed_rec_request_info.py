from datetime import datetime

from pydantic import BaseModel


class ParsingParametersApiMdl(BaseModel):
    channel_name: str
    dt_to: datetime
    dt_from: datetime
