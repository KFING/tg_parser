from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db_main.database import Base


class TgPostDbMdl(Base):
    __tablename__ = "tg_posts"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # props:
    post_id: Mapped[int] = mapped_column(nullable=False, default=0)
    tg_channel_id: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    tg_pb_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())
    content: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    link: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    # relationships:
