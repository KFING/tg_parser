from enum import Enum


class TgTaskStatus(Enum):
    completed = "completed"
    failed = "failed"
    processing = "processing"


class TgTask(Enum):
    parse = 'parse'
