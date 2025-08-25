from datetime import datetime

from sqlalchemy import DateTime, func, null, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.db_main.database import Base
from src.db_main.models.channel import ChannelDbMdl


class PostDbMdl(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # props:
    channel_id: Mapped[str] = mapped_column(ForeignKey('channels.id'), nullable=False, default=null(), server_default=null())
    post_id: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    pb_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())
    link: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    # relationships:
