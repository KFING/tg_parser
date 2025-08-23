import asyncio
import logging

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_dash.utils.streamlit import st_no_top_borders
from src.service_chat_bot import manager_chat

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.300_Chat"

@st.cache_resource
async def init_qa():
    manager_chat.file_loader_init()
    return manager_chat.initialize()

async def main() -> None:
    st.set_page_config(
        page_title="CHAT WITH CONTENT CREATORS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("CHAT WITH CONTENT CREATORS")

    message = st.chat_input("message")
    if message:
        st.write(f'U: {message}')
        qa = await init_qa()
        response = qa.invoke({"query": message})
        st.write(f"Peppi: {response["result"]}")




asyncio.run(main())
