from enum import Enum

from pydantic import BaseModel


class TelegramParserSettings(BaseModel):
    parser: str
    type_parser: str
    api_id: int
    api_hash: str
    bot_token: str
    frequency: int

class TelegramParsers(Enum):
    telethon_parser: str = "Telethon parser"
    bs_parser: str = "Bs4 parser"

class TelegramTypeParser(Enum):
    realtime_parser: str = "Realtime parser"
    full_parser: str = "Full parser"
    link_parser: str = "Link parser"
