from datetime import datetime

from sqlalchemy import DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.db_main.database import Base
from src.dto.feed_rec_info import Source


class ChannelDbMdl(Base):
    __tablename__ = "channels"
    id: Mapped[str] = mapped_column(primary_key=True, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # props:
    source: Mapped[Source] = mapped_column(Enum(Source), nullable=False)
    channel_name: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    created_channel_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    description: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    link: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    # relationships:
