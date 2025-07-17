from enum import Enum

from src.dto.feed_rec_info import Source


class RedisChannels(Enum):
    TG_PARSER = "tg_parser"
    TG_TASKS = "tg_tasks"


class RedisNamespace(Enum):
    DT_TO = "dt_to"
    DT_FROM = "dt_from"


def source_channel_name_dt_now(source: Source, channel_name: str):
    return f"{source}_{channel_name}_dt_now"


def source_channel_name_dt_to(source: Source, channel_name: str):
    return f"{source}_{channel_name}_dt_to"


def source_channel_name_dt_from(source: Source, channel_name: str):
    return f"{source}_{channel_name}_dt_from"


def source_channel_name_set(source: Source, channel_name: str):
    return f"{source}_{channel_name}_set"
