import asyncio
import logging

import aioredis
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.utils.exceptions import ChatNotFound

from tgbot.config import Settings
from tgbot.filters.admin import AdminFilter, GroupFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.user import register_user
from tgbot.handlers.payments import register_payment
from tgbot.handlers.group import register_group
from tgbot.middlewares.db import DbMiddleware
from tgbot.services.db_connection import create_session_factory
from tgbot.services.logger import setup_logger
from tgbot.services import scheduler


def register_all_middlewares(dp):
    dp.setup_middleware(DbMiddleware())


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(GroupFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_group(dp)
    register_user(dp)
    register_payment(dp)


async def set_commands(dp: Dispatcher, admin_ids: list[int]):
    await dp.bot.set_my_commands(
        commands=[BotCommand("start", "Старт")]
    )
    commands_for_admin = [
        BotCommand("start", "Старт"),
        BotCommand("add_chat", "Добавить чат (в группе)"),
        BotCommand("delete_chat", "Удалить чат"),
        BotCommand("edit_chat", "Изменить чат"),
        BotCommand("update_start_message", "Изменить приветственное сообщение")
    ]
    for admin_id in admin_ids:
        try:
            await dp.bot.set_my_commands(
                commands=commands_for_admin,
                scope=BotCommandScopeChat(admin_id)
            )
        except ChatNotFound as er:
            logging.error(f"Установка команд для администратора {admin_id}: {er}")


async def main():
    setup_logger("INFO")
    logging.info("Starting bot")
    config = Settings()
    database_url = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.name}"
    redis = aioredis.from_url("redis://localhost", decode_responses=True)

    session_factory = create_session_factory(database_url)

    storage = MemoryStorage()

    bot = Bot(token=config.tg.token, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)

    bot["config"] = config
    bot["redis"] = redis
    bot["session_factory"] = session_factory
    # bot["scheduler"] = scheduler.scheduler
    bot_info = await bot.get_me()
    logging.info(f'<yellow>Name: <b>{bot_info["first_name"]}</b>, username: {bot_info["username"]}</yellow>')

    register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)
    await set_commands(dp, config.tg.admins)
    # await scheduler.update_sending_on_start_bot(bot, session_factory)
    scheduler.creat_jobs(session_factory)

    # start
    try:
        scheduler.scheduler.start()
        await dp.start_polling()
    finally:
        await redis.close()
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
