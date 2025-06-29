from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TgTaskStatus(Enum):
    completed = "completed"
    failed = "failed"
    processing = "processing"
    free = "free"


class TgTaskEnum(Enum):
    parse = "parse"


class TgTask(BaseModel):
    channel_name: str
    dt_to: datetime
    dt_from: datetime
    status: TgTaskStatus
    task: TgTaskEnum
