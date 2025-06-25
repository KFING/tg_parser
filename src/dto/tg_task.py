from enum import Enum

from pydantic import BaseModel


class TgTaskStatus(Enum):
    completed = "completed"
    failed = "failed"
    processing = "processing"


class TgTaskEnum(Enum):
    parse = 'parse'

class TgTask(BaseModel):
    chanel_id: str
    status: TgTaskStatus
    task: TgTaskEnum
