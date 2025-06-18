import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db_main.database import Base


class UserDbMdl(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # props:
    # relationships:
