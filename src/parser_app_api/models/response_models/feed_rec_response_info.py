from pydantic import BaseModel

from src.dto.feed_rec_info import FeedRecPostFull, TmpListFeedRecPostShort


class FeedRecResponsePostsList(BaseModel):
    data: TmpListFeedRecPostShort


class FeedRecResponsePostFull(BaseModel):
    data: FeedRecPostFull
