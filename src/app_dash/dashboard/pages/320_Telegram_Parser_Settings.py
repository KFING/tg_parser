import asyncio
import json
import logging
from datetime import datetime
from enum import Enum

import streamlit as st
from pydantic import BaseModel

from src import log
from src.app_dash.dashboard.models.models import TelegramParserSettings, TelegramParsers, TelegramTypeParser
from src.app_dash.utils.streamlit import st_no_top_borders
from src.cli_scrapper.main import get_channel_posts_telegram
from src.common.moment import START_OF_EPOCH, END_OF_EPOCH
from src.dto.feed_rec_info import TmpListMedia
from src.env import SCRAPPER_RESULTS_DIR, SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG

logger = logging.getLogger(__name__)



async def main() -> None:
    st.set_page_config(
        page_title="TELEGRAM CHANNEL SCRAPER",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("TELEGRAM CHANNEL SCRAPER")
    column_parser, column_type = st.columns(2)
    json_file = json.load((SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG / "config.json").open("r"))
    tg_settings = TelegramParserSettings(
        parser=json_file["parser"],
        type_parser=json_file["type_parser"],
        api_id=int(json_file["api_id"]),
        api_hash=json_file["api_hash"],
        bot_token=json_file["bot_token"],
        frequency=int(json_file["frequency"]),
    )

    parser = column_parser.radio(
        "Take parser for telegram",
        [f"***{TelegramParsers.bs_parser.value}***", f"***{TelegramParsers.telethon_parser.value}***"],
        captions=[
            "Parser without login and api key",
            "Parser with login and api key",
        ],
    )

    if parser == f"***{TelegramParsers.telethon_parser.value}***":
        column_parser.write("You selected Telethon parser")
        column_parser.write("TELETHON PARSER")
        tg_settings.parser = TelegramParsers.telethon_parser.value
        try:
            tg_settings.api_id = int(column_parser.text_input("Api id, must be integer", help="https://my.telegram.org/auth?to=apps", value="11111111"))
            tg_settings.api_hash = column_parser.text_input("Api hash, must be string", help="https://my.telegram.org/auth?to=apps")
            tg_settings.bot_token = column_parser.text_input("Bot token, must be string", help="https://t.me/botfather")
        except ValueError:
            column_parser.write("Please enter a valid value")
        if column_parser.button("commit", key=0):
            (SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG / "config.json").write_text(tg_settings.model_dump_json(indent=4))

    else:
        column_parser.write("You selected BS4 parser.")
        column_parser.write("BS4 PARSER")
        tg_settings.parser = TelegramParsers.bs_parser.value
        tg_settings.api_id = 11111111
        tg_settings.api_hash = ""
        tg_settings.bot_token = ""
        if column_parser.button("commit", key=1):
            (SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG / "config.json").write_text(tg_settings.model_dump_json(indent=4))





    type_parser = column_type.radio(
        "Take type parser for telegram",
        [TelegramTypeParser.realtime_parser.value, TelegramTypeParser.full_parser.value, TelegramTypeParser.link_parser.value],
        captions=[
            "2 last posts on channel + realtime tg parser",
            "from start to finish",
            "Parser with login and api key",
        ],
    )

    match type_parser:
        case TelegramTypeParser.realtime_parser.value:
            column_type.write(f"You selected {TelegramTypeParser.realtime_parser.value}")
            tg_settings.type_parser = TelegramTypeParser.realtime_parser.value
            tg_settings.frequency = column_type.text_input("frequency, must be integer", help="frequency via ratelimiter, frequency request in minute", value=10)


            if column_type.button("commit", key=2):
                (SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG / "config.json").write_text(tg_settings.model_dump_json(indent=4))
        case TelegramTypeParser.full_parser.value:
            column_type.write(f"You selected {TelegramTypeParser.full_parser.value}")
            tg_settings.type_parser = TelegramTypeParser.full_parser.value
            tg_settings.frequency = column_type.text_input("frequency, must be integer", help="frequency via ratelimiter, frequency request in minute", value=10)
            if column_type.button("commit", key=3):
                (SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG / "config.json").write_text(tg_settings.model_dump_json(indent=4))
        case TelegramTypeParser.link_parser.value:
            st.write(f"You selected {TelegramTypeParser.link_parser.value}")
            tg_settings.type_parser = TelegramTypeParser.link_parser.value
            if column_type.button("commit", key=4):
                (SCRAPPER_SESSION_DIR_TELEGRAM_CONFIG / "config.json").write_text(tg_settings.model_dump_json(indent=4))





asyncio.run(main())
