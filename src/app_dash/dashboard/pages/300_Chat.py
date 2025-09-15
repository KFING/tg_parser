import asyncio
import logging
from datetime import datetime

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_api.dependencies import DBM
from src.app_dash.run_dash_page import run_dash_page
from src.app_dash.utils.streamlit import st_no_top_borders
from src.db_main.cruds import channel_crud
from src.dto.feed_rec_info import Source
from src.service_chat_bot import manager_chat
from src.service_deepseek import prompts

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.300_Chat"

@st.cache_resource
def init_qa(source: Source, channel_name: str):
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
                st.session_state.src = src
        with st.form("settings"):
            channel = st.selectbox("Channel", [channel.channel_name for channel in channels])
            if not st.form_submit_button('submit') and not channel:
                return
            st.session_state.channel = channel
            st.session_state.flag_form = True
    if 'qa' not in st.session_state and 'src' in st.session_state:
        qa = init_qa(Source(st.session_state.src), st.session_state.channel)
        st.session_state.qa = qa
    if 'qa' in st.session_state:
        st.write(f"channel: {st.session_state.channel}")


        message = st.chat_input("message")
        if message:
            st.write(f'You: {message}')
            st.write(f'time: {datetime.now()}')
            qa = st.session_state.qa
            response = qa.invoke({"query": prompts.realtime_answer(message)})
            st.write(f'Nothing: {response["result"]}')
            st.write(f'time: {datetime.now()}')



run_dash_page(mdl_name, main)
