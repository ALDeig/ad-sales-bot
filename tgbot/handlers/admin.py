import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services import service, db_queries
from tgbot.services.datatypes import ChatData
from tgbot.services.db_queries import get_chats, delete_chat, add_message, add_user, get_message
from tgbot.keyboards import kb_admin, kb_user


def check_msg_price(msg_text: str) -> int | None:
    try:
        price = int(msg_text)
    except ValueError:
        return
    return price


async def user_start(msg: Message, db: AsyncSession, state: FSMContext):
    await state.finish()
    await add_user(db, msg.from_user.id, msg.from_user.username)
    start_message = await get_message(db, "start")
    kb = kb_user.buy_ad()
    await msg.answer(start_message.message if start_message else "Стартовое сообщение", reply_markup=kb)


# Добавление чата
async def cmd_add_chat(msg: Message):
    try:
        await msg.delete()
    except Exception as er:
        logging.error(er)
    amount_members = await msg.chat.get_members_count()
    kb = kb_admin.add_chat(msg.chat.id)
    await msg.bot.send_message(
        msg.from_user.id,
        f"Новая группа: {msg.chat.title}\nКоличество участников в группе - {amount_members}.", reply_markup=kb)


async def btn_add_chat(call: CallbackQuery, state: FSMContext):
    await call.answer()
    chat_id = call.data.split(":")[1]
    chat = await call.bot.get_chat(chat_id)
    chat_data = ChatData(chat_id=chat_id, name=chat.title)
    await state.update_data(chat_data=chat_data)
    await call.message.answer("Через какое количество постов должна появляться реклама?")
    await state.set_state("get_amount_posts")


async def get_amount_posts(msg: Message, state: FSMContext):
    amount = check_msg_price(msg.text)
    if not amount:
        await msg.answer("Ответ должен быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.amount_posts = amount
    await state.update_data(chat_data=chat_data)
    await msg.answer("Введите цену за месяц")
    await state.set_state("price_month")


async def price_month(msg: Message, state: FSMContext):
    price = check_msg_price(msg.text)
    if not price:
        await msg.answer("Цена должна быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.price_month = price
    await state.update_data(chat_data=chat_data)
    await msg.answer("Введите цену за 3 месяца")
    await state.set_state("price_3_month")


async def price_three_month(msg: Message, state: FSMContext):
    price = check_msg_price(msg.text)
    if not price:
        await msg.answer("Цена должна быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.price_three_month = price
    await state.update_data(chat_data=chat_data)
    await msg.answer(f"Введите цену за неделю")
    await state.set_state("price_week")


async def price_week(msg: Message, db, state: FSMContext):
    price = check_msg_price(msg.text)
    if not price:
        await msg.answer("Цена должна быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.price_week = price
    await service.add_chat(db, chat_data)
    await msg.answer("Готово")
    await state.finish()


# async def price_two_post_month(msg: Message, state: FSMContext):
#     price = check_msg_price(msg.text)
#     if not price:
#         await msg.answer("Цена должна быть числом")
#         return
#     chat_data: ChatData = (await state.get_data()).get("chat_data")
#     chat_data.price_month_two_post = price
#     await state.update_data(chat_data=chat_data)
#     await msg.answer(f"Введите цену за 3 поста на месяц")
#     await state.set_state("price_three_post_month")
#
#
# async def price_three_post_month(msg: Message, state: FSMContext):
#     price = check_msg_price(msg.text)
#     if not price:
#         await msg.answer("Цена должна быть числом")
#         return
#     chat_data: ChatData = (await state.get_data()).get("chat_data")
#     chat_data.price_month_three_post = price
#     await state.update_data(chat_data=chat_data)
#     await msg.answer(f"Введите цену за 1 пост на неделю")
#     await state.set_state("price_one_post_week")
#
#
# async def price_one_post_week(msg: Message, state: FSMContext):
#     price = check_msg_price(msg.text)
#     if not price:
#         await msg.answer("Цена должна быть числом")
#         return
#     chat_data: ChatData = (await state.get_data()).get("chat_data")
#     chat_data.price_week_one_post = price
#     await state.update_data(chat_data=chat_data)
#     await msg.answer(f"Введите цену за 2 поста на неделю")
#     await state.set_state("price_two_post_week")
#
#
# async def price_two_post_week(msg: Message, state: FSMContext):
#     price = check_msg_price(msg.text)
#     if not price:
#         await msg.answer("Цена должна быть числом")
#         return
#     chat_data: ChatData = (await state.get_data()).get("chat_data")
#     chat_data.price_week_two_post = price
#     await state.update_data(chat_data=chat_data)
#     await msg.answer(f"Введите цену за 3 поста на неделю")
#     await state.set_state("price_three_post_week")
#
#
# async def price_three_post_week(msg: Message, db, state: FSMContext):
#     price = check_msg_price(msg.text)
#     if not price:
#         await msg.answer("Цена должна быть числом")
#         return
#     chat_data: ChatData = (await state.get_data()).get("chat_data")
#     chat_data.price_week_three_post = price
#     await service.add_chat(db, chat_data)
#     await msg.answer("Готово")
#     await state.finish()


# Удаление чата
async def cmd_delete_chat(msg: Message, db, state: FSMContext):
    chats = await get_chats(db)
    kb = kb_admin.select_chat(chats)
    await msg.answer("Выберите чат", reply_markup=kb)
    await state.set_state("select_chat_for_delete")


async def select_group_for_delete(call: CallbackQuery, db, state: FSMContext):
    await call.answer()
    await delete_chat(db, call.data)
    await call.message.edit_reply_markup()
    await call.message.answer("Готово")
    await state.finish()


# Обновить чат
async def update_chat(msg: Message, db, state: FSMContext):
    chats = await get_chats(db)
    kb = kb_admin.select_chat(chats)
    await msg.answer("Выберите чат", reply_markup=kb)
    await state.set_state("select_chat_for_update")


async def select_chat_for_update(call: CallbackQuery, state: FSMContext):
    await call.answer()
    chat_data = ChatData()
    chat_data.chat_id = call.data
    await state.update_data(chat_data=chat_data)
    amount_members = await call.bot.get_chat_members_count(call.data)
    await call.message.answer(f"Количество участников в группе - {amount_members}. Введите цену за месяц")
    await state.set_state("price_month")


async def cmd_update_start_message(msg: Message, state: FSMContext):
    await msg.answer("Введите сообщение")
    await state.set_state("get_text_for_start_message")


async def get_text_for_start_message(msg: Message, db, state: FSMContext):
    await add_message(db, "start", msg.text)
    await msg.answer("Готово")
    await state.finish()


async def cmd_get_promo_code(msg: Message, db: AsyncSession):
    promo_code = service.generate_promo_code(8)
    await msg.answer(promo_code)
    await add_message(db, "promo_code", promo_code)


async def cmd_add_group_user(msg: Message, state: FSMContext):
    await msg.answer("Введите id пользователя")
    await state.set_state("get_id_group_user")


async def get_id_group_user(msg: Message, db: AsyncSession, state: FSMContext):
    try:
        user_id = int(msg.text)
    except ValueError:
        await msg.answer("ID должен быть числом")
        return
    await db_queries.add_group_user(db, user_id, True)
    await state.finish()
    await msg.answer("Готово")


async def cmd_delete_my_ads(msg: Message, db: AsyncSession, state: FSMContext):
    my_ads = await db_queries.get_sendings_by_user(db, msg.from_user.id)
    messages = []
    for my_ad in my_ads:
        kb = kb_admin.select_sending(my_ad)
        sent_msg = await msg.answer(
            f"Название кнопки: {my_ad.button_title}\nСсылка: {my_ad.button_link}", reply_markup=kb
        )
        messages.append(sent_msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state("select_ad_for_delete")


async def btn_select_ad_for_delete(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    await db_queries.delete_sending(db, call.data)
    data = await state.get_data()
    for message in data["messages"]:
        await call.bot.delete_message(call.from_user.id, int(message))
    await call.message.answer("Готово")
    await state.finish()


def register_admin(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(cmd_add_chat, commands=["add_chat"], is_admin=True)
    dp.register_callback_query_handler(btn_add_chat, lambda call: call.data.startswith("add"))
    dp.register_message_handler(get_amount_posts, state="get_amount_posts")
    dp.register_message_handler(price_month, state="price_month")
    dp.register_message_handler(price_three_month, state="price_3_month")
    dp.register_message_handler(price_week, state="price_week")
    dp.register_message_handler(cmd_delete_chat, commands=["delete_chat"], is_admin=True)
    dp.register_callback_query_handler(select_group_for_delete, state="select_chat_for_delete")
    dp.register_message_handler(update_chat, commands=["edit_chat"], is_admin=True)
    dp.register_callback_query_handler(select_chat_for_update, state="select_chat_for_update")
    dp.register_message_handler(cmd_update_start_message, commands=["update_start_message"])
    dp.register_message_handler(get_text_for_start_message, state="get_text_for_start_message")
    dp.register_message_handler(cmd_get_promo_code, commands=["get_promo_code"], is_admin=True)
    dp.register_message_handler(cmd_add_group_user, commands=["add_group_user"])
    dp.register_message_handler(get_id_group_user, state="get_id_group_user")
    dp.register_message_handler(cmd_delete_my_ads, commands=["delete_ads"])
    dp.register_callback_query_handler(btn_select_ad_for_delete, state="select_ad_for_delete")
