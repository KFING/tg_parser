import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.user import UserDbMdl


async def create_user(db: AsyncSession, user_id: uuid.UUID) -> UserDbMdl:
    user = UserDbMdl(id=user_id)
    db.add(user)
    await db.commit()
    return user


async def get_all_users(db: AsyncSession) -> Sequence[UserDbMdl]:
    users = await db.execute(select(UserDbMdl))
    return users.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> UserDbMdl | None:
    return await db.get(UserDbMdl, user_id)
