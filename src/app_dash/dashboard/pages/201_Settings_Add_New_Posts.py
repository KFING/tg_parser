import logging
from datetime import datetime

import streamlit as st
from redis.asyncio import Redis

from src.app_api.dependencies import DBM
from src.app_dash.run_dash_page import run_dash_page
from src.app_dash.utils.streamlit import st_no_top_borders
from src.common.moment import END_OF_EPOCH, START_OF_EPOCH
from src.dto.feed_rec_info import Source
from src.dto.redis_models import RedisTask

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.201_Settings_Add_New_Posts"


async def main(dbm: DBM, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="FORM VIA ADD NEW POSTS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("FORM VIA ADD NEW POSTS")
    default_source = st.query_params.get("source", "")
    default_channel_name = st.query_params.get("channel_name", "")
    with st.form("TASK"):
        match default_source:
            case Source.YOUTUBE.value:
                source = Source.YOUTUBE
            case Source.TELEGRAM.value:
                source = Source.TELEGRAM
            case _:
                source = st.selectbox("Source", (Source.YOUTUBE, Source.TELEGRAM))
        channel_name = st.text_input("Channel name", help="t.me/CHANNEL_NAME", value=default_channel_name)
        time_period = st.date_input("Select time period", (START_OF_EPOCH, END_OF_EPOCH), START_OF_EPOCH, END_OF_EPOCH, format="MM.DD.YYYY")
        if not st.form_submit_button("CREATE"):
            return

    with st.spinner("wait few seconds..."):
        if isinstance(time_period, tuple) and len(time_period) == 2:
            start_of_epoch = datetime(time_period[0].year, time_period[0].month, time_period[0].day)
            end_of_epoch = datetime(time_period[-1].year, time_period[-1].month, time_period[-1].day)
            await rds.sadd(str(RedisTask.channel_tasks.value), f"{source.value}${channel_name}")
            await rds.rpush(f"{source.value}${channel_name}", str(start_of_epoch), str(end_of_epoch))
            st.write(await rds.lrange(f"{source.value}${channel_name}", 0, -1))

        else:
            st.write("WARNING: time period is invalid")
            return


run_dash_page(mdl_name, main)
