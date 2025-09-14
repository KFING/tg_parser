import asyncio
import logging

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_api.dependencies import DBM
from src.app_dash.run_dash_page import run_dash_page
from src.app_dash.utils.streamlit import st_no_top_borders
from src.db_main.cruds import channel_crud
from src.dto.feed_rec_info import Source
from src.service_chat_bot import manager_chat

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.300_Chat"

@st.cache_resource
async def init_qa(source: Source, channel_name: str):
    return manager_chat.initialize_retriever(source, channel_name)

async def main(dbm: DBM, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="CHAT WITH CONTENT CREATORS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("CHAT WITH CONTENT CREATORS")


    if 'flag_form' not in st.session_state:
        st.session_state.flag_form = False
    if not st.session_state.flag_form:
        src = st.selectbox("Source", (Source.YOUTUBE, Source.TELEGRAM))
        st.write(f"src: {src}")
        async with dbm.session() as session:
            with st.spinner("wait few seconds..."):
                channels = await channel_crud.get_channels_by_source(session, src)
        with st.form("settings"):
            channel = st.selectbox("Channel", [channel.channel_name for channel in channels])
            if not st.form_submit_button('submit') and not channel:
                return
            st.session_state.flag_form = True
    if 'qa' not in st.session_state:
        st.session_state.qa = await init_qa(src, channel)
    st.write(f"channel: {channel}")


    message = st.chat_input("message")
    if message:
        st.write(f'U: {message}')
        qa = st.session_state.qa
        """response = qa.invoke({"input": message})
        st.write(f"dupler: {message}")
        st.write(f"Peppi: {response["result"]}")"""



run_dash_page(mdl_name, main)
