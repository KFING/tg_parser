import asyncio
import logging
from datetime import datetime

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_dash.utils.streamlit import st_no_top_borders
from src.common.moment import END_OF_EPOCH, START_OF_EPOCH
from src.db_main.cruds import post_crud
from src.dto.post import Source
from src.dto.redis_task import RedisTask

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.100_Task"


async def main(*, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="CHAT SETTINGS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("CHAT SETTINGS")
    src_col, channel_col, button_col = st.columns((0.45,0.45, 0.1))
    source = src_col.selectbox("Source", (Source.YOUTUBE, Source.TELEGRAM))
    if not isinstance(source, Source):
        return
    with st.spinner("wait few seconds..."):
        posts = post_crud.get_channels_posts(db, source)
    channel_col.markdown(
        f"""
                    <a href="/Settings_New?source={source}">add new</a>
                """,
        unsafe_allow_html=True,
    )
    for post in posts:
        channel_col.write(f"CHANNEL NAME: {post.channel_name}", divider="red")
        button_col.markdown(
            f"""
                <a href="/Settings_About?source={source}&channel={post.channel_name}">about it</a>
            """,
            unsafe_allow_html=True,
        )


with log.scope(logger, mdl_name) as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
