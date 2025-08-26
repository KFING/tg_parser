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
from src.db_main.cruds import channel_crud, post_crud
from src.dto.feed_rec_info import Source

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.203_Settings_About"


async def main(dbm: DBM, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="ABOUT CHANNEL",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("ABOUT CHANNEL")
    default_source = st.query_params.get("source", "")
    default_channel_name = st.query_params.get("channel_name", "")
    if (not default_source) or (not default_channel_name):
        with st.form("ABOUT"):
            source = st.selectbox("Source", (Source.YOUTUBE, Source.TELEGRAM))
            channel_name = st.text_input("Channel name", help="t.me/CHANNEL_NAME")
            if not st.form_submit_button("find"):
                return
    else:
        match default_source:
            case Source.YOUTUBE.value:
                source = Source.YOUTUBE
            case Source.TELEGRAM.value:
                source = Source.TELEGRAM
        channel_name = default_channel_name
    async with dbm.session() as session:
        channel = await channel_crud.get_channel_by_source_by_channel_name(session, source, channel_name)
        posts = await post_crud.get_posts_by_channel_id(session, channel.id)
    with st.spinner("wait few seconds..."):
        st.write(f"description: {channel.description}")
        st.write(f"author: {channel.author}")
        len_posts = len(posts)
        st.write(f"uploaded of posts: {len_posts}")
        if len_posts != 0:
            st.write(f"from{posts[0].pb_date} to {posts[-1].pb_date}")
        st.markdown(
            f"""
                            <a href="/Settings_New_Timeperiod?source={source}&channel_name={channel_name}">add time period</a>
                        """,
            unsafe_allow_html=True,
        )




run_dash_page(mdl_name, main)
