from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class RedisTask(Enum):
    channel_tasks= 'channel_tasks',
    counter_of_workers='cow'

class Task(BaseModel):
    source: str
    channel_name: str
    dt_to: datetime
    dt_from: datetime
