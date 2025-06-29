import contextlib
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.env import DB_URL


# Heavily inspired by https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
class DBM:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None) -> None:
        engine_kwargs = engine_kwargs or {}
        self._engine: AsyncEngine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine, expire_on_commit=False)

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close_connection(self) -> None:
        await self._engine.dispose()


_db: DBM | None = None


def get_db_main_manager(new_connection: bool = False) -> DBM:
    if new_connection:
        return DBM(str(DB_URL))

    global _db  # noqa: PLW0603
    if _db is None:
        _db = DBM(str(DB_URL))
    return _db


async def get_db_main() -> AsyncIterator[AsyncSession]:
    db = get_db_main_manager()
    async with db.session() as session:
        yield session
