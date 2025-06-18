import asyncio
import logging
from datetime import datetime

import streamlit as st
from telethon import TelegramClient

from src import log
from src.app_dash.utils.streamlit import st_no_top_borders
from src.common.moment import END_OF_EPOCH, START_OF_EPOCH
from src.dto.feed_rec_info import FeedRecPostShort, TmpListMedia
from src.env import SCRAPPER_SESSION_DIR__TELEGRAM
from src.external_telegram import telegram_scrapy

logger = logging.getLogger(__name__)


@st.cache_resource
async def get_channel_posts_telegram(channel_id: str, dt_from: datetime, dt_to: datetime, *, log_extra: dict[str, str]) -> list[FeedRecPostShort]:
    tg = TelegramClient(SCRAPPER_SESSION_DIR__TELEGRAM / st.session_state.tg_phone, int(st.session_state.tg_api_id), st.session_state.tg_api_hash)
    if "tg_code" in st.session_state:
        await tg.start(phone=st.session_state.tg_phone, password=st.session_state.password, code_callback=code_auth)  # pyright: ignore
    else:
        await tg.start(phone=st.session_state.tg_phone, password=st.session_state.password)  # pyright: ignore
    return [i async for i in telegram_scrapy.get_posts_list(tg, channel_id, dt_from, dt_to, log_extra=log_extra)]


def code_auth() -> str:
    assert isinstance(st.session_state.tg_code, str)
    return st.session_state.tg_code


@st.cache_resource
async def tg_auth_resource(phone: str, api_id: str, api_hash: str) -> TelegramClient | None:
    tg = TelegramClient(SCRAPPER_SESSION_DIR__TELEGRAM / phone, int(api_id), api_hash)

    if not tg.is_connected():
        await tg.connect()

    await tg.send_code_request(phone=phone)
    st.session_state.is_tg_client = True

    tg.disconnect()

    return tg


async def auth() -> None:
    if "is_tg_client" not in st.session_state:
        with st.form("AUTH"):
            phone = st.text_input("phone")
            api_id = st.text_input("api_id")
            api_hash = st.text_input("api_hash")
            password = st.text_input("password", help="if you have tfa password")
            if not st.form_submit_button("submit"):
                return
            st.session_state.tg_phone = phone
            st.session_state.tg_api_id = api_id
            st.session_state.tg_api_hash = api_hash
            st.session_state.password = password
        if (SCRAPPER_SESSION_DIR__TELEGRAM / f"{phone}.session").exists():
            (SCRAPPER_SESSION_DIR__TELEGRAM / f"{phone}.session").unlink()
            logger.info("old session has been deleted")
        await tg_auth_resource(phone, api_id, api_hash)
        st.rerun()
    else:
        if st.session_state.is_tg_client:
            with st.form("LOGIN"):
                code = st.text_input("code")
                if not st.form_submit_button("submit"):
                    return
            st.session_state.tg_code = code

        st.session_state.tg_session = True


async def main(*, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="TELEGRAM CHANNEL SCRAPER",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("TELEGRAM CHANNEL SCRAPER")
    if "tg_session" in st.session_state:
        with st.form("POST"):
            channel_id = st.text_input("Channel ID", help="@CHANNEL_ID")
            time_period = st.date_input("Select time period", (START_OF_EPOCH, END_OF_EPOCH), START_OF_EPOCH, END_OF_EPOCH, format="MM.DD.YYYY")
            if not st.form_submit_button("find"):
                return
        with st.spinner("wait few seconds..."):
            if isinstance(time_period, tuple) and len(time_period) == 2:
                start_of_epoch = datetime(time_period[0].year, time_period[0].month, time_period[0].day)
                end_of_epoch = datetime(time_period[-1].year, time_period[-1].month, time_period[-1].day)
                posts = await get_channel_posts_telegram(channel_id, start_of_epoch, end_of_epoch, log_extra=log_extra)
            else:
                st.write("WARNING: time period is invalid")
                return
        for i, post in enumerate(posts):
            st.header(f"POST {i + 1}/{len(posts)}:", divider="blue")
            st.write(f"  TITLE: {post.title}")
            st.write(f"  POST ID: {post.post_id}")
            st.write(f"  PUBLISHED DATE: {post.posted_at!s}")
            st.write(f"  LINK: {post.url}")
            st.write("  MEDIA: ")
            st.json(TmpListMedia(media=post.media).model_dump_json(indent=4))
    else:
        try:
            await auth()
        except Exception:
            st.session_state.tg_session = False


with log.scope(logger, "Telegram_post") as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
