from datetime import timedelta, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import sessionmaker

from tgbot.services import db_queries
# from tgbot.services.service import update_sending

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def job_for_delete_sendings(session_factory: sessionmaker, admin_ids: list):
    async with session_factory() as session:
        await db_queries.delete_old_sending(session, admin_ids)
        await db_queries.delete_group_user(session, datetime.now() - timedelta(days=3))


# async def update_sending_on_start_bot(bot, session_factory):
#     async with session_factory() as session:
#         sendings = await db_queries.get_all_sendings(session)
#         for sending in sendings:
#             await update_sending(session, bot, scheduler, sending)


def creat_jobs(session_factory, admin_ids: list):
    # scheduler.add_job(job_for_delete_sendings, "cron", hour=1, args=[session_factory, admin_ids])
    scheduler.add_job(job_for_delete_sendings, "cron", hour=1, minute=0, args=[session_factory, admin_ids])
