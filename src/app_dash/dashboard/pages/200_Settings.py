import asyncio
import logging
from datetime import datetime

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_api.dependencies import DBM
from src.app_dash.run_dash_page import run_dash_page
from src.app_dash.utils.streamlit import st_no_top_borders
from src.common.moment import END_OF_EPOCH, START_OF_EPOCH
from src.db_main.cruds import post_crud, channel_crud
from src.dto.feed_rec_info import Source

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.200_Settings"


async def main(dbm: DBM, log_extra: dict[str, str]) -> None:
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
    async with dbm.session() as session:
        with st.spinner("wait few seconds..."):
            channels = await channel_crud.get_channels_by_source(session, source)
        channel_col.markdown(
            f"""
                                <a href="/Settings_Add_New_Channel?source={source}">add channel</a>
                            """,
            unsafe_allow_html=True,
        )

        for channel in channels:
            channel_col.write(f"CHANNEL NAME: {channel.channel_name}", divider="red")
            button_col.markdown(
                f"""
                    <a href="/Settings_About?source={source}&channel={channel.channel_name}">about it</a>
                """,
                unsafe_allow_html=True,
            )


run_dash_page(mdl_name, main)
