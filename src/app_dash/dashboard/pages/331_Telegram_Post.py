import asyncio
import logging
from pathlib import Path

import streamlit as st
from telethon import TelegramClient
from src import log
from src.app_dash.utils.streamlit import st_no_top_borders
from src.dto.download_post_recipe import DownloadPostContentRecipe, DownloadQuality
from src.dto.feed_rec_info import FeedRecPostFull, Lang, MediaFormat
from src.env import SCRAPPER_SESSION_DIR__TELEGRAM
from src.external_telegram import telegram_scrapy

logger = logging.getLogger(__name__)

@st.cache_resource
async def download_post_telegram(
    post_id: str, lang: Lang, preview_image: bool, video_quality: DownloadQuality | None, image_quality: DownloadQuality | None, *, log_extra: dict[str, str]
) -> FeedRecPostFull | None:
    tg = TelegramClient(SCRAPPER_SESSION_DIR__TELEGRAM / st.session_state.tg_phone, int(st.session_state.tg_api_id), st.session_state.tg_api_hash)
    if "tg_code" in st.session_state:
        await tg.start(phone=st.session_state.tg_phone, password=st.session_state.password, code_callback=code_auth)  # pyright: ignore
    else:
        await tg.start(phone=st.session_state.tg_phone, password=st.session_state.password)  # pyright: ignore
    return await telegram_scrapy.download_post(
        tg,
        post_id,
        DownloadPostContentRecipe(
            lang=lang,
            content=False,
            captions=False,
            timeline=False,
            download_preview_image=preview_image,
            download_document=False,
            download_video_quality=video_quality,
            download_audio_quality=None,
            download_image_quality=image_quality,
        ),
        log_extra=log_extra,
    )


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
        page_title="TELEGRAM POST SCRAPER",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("TELEGRAM POST SCRAPER")
    if "tg_session" in st.session_state:
        with st.form("POST"):
            post_id = st.text_input("Post_ID", help="https://www.instagram.com/p/POST_ID")
            lang = st.selectbox("language", (Lang.RU, Lang.EN))
            preview_image = st.checkbox("preview image")
            video_quality = st.selectbox("video_quality", (None, DownloadQuality.LOW, DownloadQuality.MEDIUM, DownloadQuality.BEST))
            image_quality = st.selectbox("image_quality", (None, DownloadQuality.LOW, DownloadQuality.MEDIUM, DownloadQuality.BEST))

            if not st.form_submit_button("find"):
                return
        with st.spinner("wait few seconds..."):
            post = await download_post_telegram(post_id, lang, preview_image, video_quality, image_quality, log_extra=log_extra)
        if post:
            st.header(f"TITLE: {post.title}", divider="blue")
            for media in post.media:
                if media.format == MediaFormat.MP4 and isinstance(media.downloaded_file, Path):
                    video_file = media.downloaded_file.open("rb")
                    video_bytes = video_file.read()
                    st.video(video_bytes)
                if media.format == MediaFormat.JPG and isinstance(media.downloaded_file, Path):
                    image_file = media.downloaded_file.open("rb")
                    image_bytes = image_file.read()
                    st.image(image_bytes)
            st.subheader(f" DESCRIPTION: {post.contents[0].content}")
            st.write(f" PUBLISHED DATE: {post.posted_at!s}")
            st.write(f" LINK: {post.url}")
    else:
        try:
            await auth()
        except Exception:
            st.session_state.tg_channel_session = False


with log.scope(logger, "Telegram_post") as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
