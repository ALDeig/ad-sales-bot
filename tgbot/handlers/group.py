import asyncio
import re
from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from aiogram.utils.exceptions import BadRequest, MessageCantBeEdited
from aioredis.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards.kb_group import emojis_kb
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


async def send_ads(redis: Redis, session: AsyncSession, msg: types.Message):
    sendings = await db_queries.get_sendings_by_chat(session, str(msg.chat.id))
    if not sendings:
        return
    kb = kb_ads_buttons(sendings)
    await redis.delete(str(msg.chat.id))
    try:
        await msg.answer("Реклама", reply_markup=kb)
    except BadRequest:
        pass


def delete_link_in_text(text: str) -> str:
    pattern = re.compile(r"http\S+|@\S+|@\s\S+")
    clear_text = re.sub(pattern, "", text)
    return clear_text


async def edit_message(msg: types.Message):
    if "text" in msg:
        text = delete_link_in_text(msg.text)
        if text != msg.text:
            try:
                await msg.edit_text(text)
            except MessageCantBeEdited:
                await msg.delete()
    elif "caption" in msg:
        caption = delete_link_in_text(msg.caption)
        if caption != msg.caption:
            try:
                await msg.edit_caption(caption)
            except MessageCantBeEdited:
                await msg.delete()


async def get_new_message(msg: types.Message, db: AsyncSession):
    redis = msg.bot.get("redis")
    check_result = await check_count_messages(redis, db, str(msg.chat.id))
    if check_result:
        await send_ads(redis, db, msg)


async def check_allowed_user(session: AsyncSession, user_id: int) -> bool:
    check = await db_queries.get_group_user(session, user_id)
    if check:
        return True
    return False


async def get_message_in_group(msg: types.Message, db: AsyncSession, state: FSMContext):
    redis = msg.bot.get("redis")
    if msg.from_user.username == "GroupAnonymousBot":
        result_check_count_message = await check_count_messages(redis, db, str(msg.chat.id))
        if result_check_count_message:
            await send_ads(redis, db, msg)
        return
    user = await db_queries.get_group_user(db, msg.from_user.id)
    if user:
        if not user.allow_ads:
            await edit_message(msg)
        result_check_count_message = await check_count_messages(redis, db, str(msg.chat.id))
        if result_check_count_message:
            await send_ads(redis, db, msg)
        return
    await msg.delete()
    kb, right_emoji = emojis_kb(msg.from_user.id)
    text = f"❗️ВАЖНО: {msg.from_user.first_name}, если ты не БОТ и не СПАМЕР, пройди проверку, нажав на кнопку, \
где есть {right_emoji}"
    new_message = await msg.answer(text, reply_markup=kb)
    await state.set_state("check")
    await asyncio.sleep(30)
    data = await state.get_data()
    if data.get("status") is None:
        await new_message.delete()
    await state.finish()


async def check_selected_emoji(call: types.CallbackQuery, db: AsyncSession, state: FSMContext):
    await state.finish()
    if int(call.data):
        await db_queries.add_group_user(db, call.from_user.id, False, datetime.now())
        status = True
    else:
        status = False
    await call.message.delete()
    await state.update_data(status=status)


def register_group(dp: Dispatcher):
    dp.register_message_handler(
        get_message_in_group,
        is_group=True,
        content_types=[
            ContentType.VIDEO, ContentType.VENUE, ContentType.TEXT, ContentType.PHOTO, ContentType.POLL,
            ContentType.DOCUMENT, ContentType.DICE, ContentType.AUDIO, ContentType.VOICE,
            ContentType.STICKER,
        ],
        state="*")
    dp.register_callback_query_handler(check_selected_emoji, state="check")

