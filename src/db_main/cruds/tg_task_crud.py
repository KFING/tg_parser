from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.tg_task import TgTaskDbMdl
from src.dto.tg_task import TgTask, TgTaskStatus


async def create_tg_task(db: AsyncSession, tg_task: TgTask) -> TgTaskDbMdl:
    tg_post = TgTaskDbMdl(
        channel_name=tg_task.channel_name,
        tg_dt_to=tg_task.dt_to,
        tg_dt_from=tg_task.dt_from,
        status=tg_task.status,
        task=tg_task.task,
    )
    db.add(tg_post)
    await db.commit()
    return tg_post


async def get_task_by_status(db: AsyncSession, status: TgTaskStatus) -> TgTaskDbMdl:
    invoices = await db.execute(select(TgTaskDbMdl).where(TgTaskDbMdl.status == status))
    return invoices.scalars().first()


async def update_task_status(db: AsyncSession, tg_task: TgTaskDbMdl, status: TgTaskStatus) -> None:
    await db.execute(update(TgTaskDbMdl).where(TgTaskDbMdl.id == tg_task.id).values(status=status))
    await db.commit()
