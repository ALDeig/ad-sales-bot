from aiogram import types, Dispatcher
from aiogram.utils.exceptions import BadRequest
from aioredis.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services import db_queries
from tgbot.keyboards.kb_sendigs import kb_ads_buttons


async def check_count_messages(redis: Redis, session: AsyncSession, chat_id: str) -> bool | None:
    chat_info = await redis.hgetall(chat_id)
    if not chat_info:
        chat = await db_queries.get_chat(session, chat_id)
        if not chat:
            return
        await redis.hset(chat_id, mapping={"count": 1, "amount_post": chat.amount_posts})
        return
    if int(chat_info["count"]) + 1 == int(chat_info["amount_post"]):
        await redis.hset(chat_id, mapping={"count": 0, "amount_post": chat_info["amount_post"]})
        return True
    await redis.hset(chat_id, mapping={"count": int(chat_info["count"]) + 1, "amount_post": chat_info["amount_post"]})


async def get_new_message(msg: types.Message, db: AsyncSession):
    redis = msg.bot.get("redis")
    check_result = await check_count_messages(redis, db, str(msg.chat.id))
    if check_result:
        sendings = await db_queries.get_sendings(db, str(msg.chat.id))
        if not sendings:
            return
        kb = kb_ads_buttons(sendings)
        await redis.delete(str(msg.chat.id))
        try:
            await msg.answer("Реклама", reply_markup=kb)
        except BadRequest:
            pass


def register_group(dp: Dispatcher):
    dp.register_message_handler(get_new_message, is_group=True, state="*")
