from enum import Enum


class RedisChannels(Enum):
    TG_PARSER = "tg_parser"
    TG_TASKS = "tg_tasks"


class RedisNamespace(Enum):
    DT_TO = "dt_to"
    DT_FROM = "dt_from"
