from datetime import datetime

from sqlalchemy import DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.db_main.database import Base
from src.dto.tg_task import TgTask, TgTaskStatus


class TgTaskDbMdl(Base):
    __tablename__ = "tg_tasks"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # props:
    channel_name: Mapped[str] = mapped_column(nullable=False, default="", server_default="")
    status: Mapped[TgTaskStatus] = mapped_column(Enum(TgTaskStatus), nullable=False)
    task: Mapped[TgTask] = mapped_column(Enum(TgTask), nullable=False)
    # relationships:
