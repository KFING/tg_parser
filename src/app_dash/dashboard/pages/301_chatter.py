import asyncio
import logging

import streamlit as st
from redis.asyncio import Redis

from src.app_dash.utils.streamlit import st_no_top_borders
from src.service_chat_bot import manager_chat

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.301_chatter"


@st.cache_resource
async def init_qa():
    return manager_chat.initialize_retriever()


async def main() -> None:
    st.set_page_config(
        page_title="CHAT WITH CONTENT CREATORS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("CHAT WITH CONTENT CREATORS")
    embedding_list = manager_chat.file_loader_init()
    print(type(embedding_list))
    print("-------------------------------------")
    print(len(embedding_list))
    print("-------------------------------------")
    print(embedding_list)
    print("-------------------------------------")
    print(embedding_list[0])
    print("-------------------------------------")
    print(embedding_list[-1])


asyncio.run(main())
