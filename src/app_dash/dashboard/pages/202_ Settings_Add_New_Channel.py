import logging

import streamlit as st
from redis.asyncio import Redis

from src.app_api.dependencies import DBM
from src.app_dash.run_dash_page import run_dash_page
from src.app_dash.utils.streamlit import st_no_top_borders
from src.cli_scrapper import scrapy_manager
from src.db_main.cruds import channel_crud
from src.dto.feed_rec_info import Channel, Source

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.202_Settings_Add_New_Channel"


async def main(dbm: DBM, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="FORM VIA ADD NEW CHANNEL",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("FORM VIA ADD NEW CHANNEL")
    default_source = st.query_params.get("source", "")
    with st.form("TASK"):
        match default_source:
            case Source.YOUTUBE.value:
                source = Source.YOUTUBE
            case Source.TELEGRAM.value:
                source = Source.TELEGRAM
            case _:
                source = st.selectbox("Source", (Source.YOUTUBE, Source.TELEGRAM))
        channel_name = st.text_input("Channel name", help="t.me/CHANNEL_NAME")
        if not st.form_submit_button("ADD"):
            return

    with st.spinner("wait few seconds..."):
        channel = await scrapy_manager.get_channel_info(source, channel_name)
        if not isinstance(channel, Channel):
            return
        async with dbm.session() as session:
            await channel_crud.add_channel(
                session,
                Channel(
                    source=channel.source, channel_name=channel.channel_name, channel_id=channel.channel_id, description=channel.description, link=channel.link
                ),
            )


run_dash_page(mdl_name, main)
