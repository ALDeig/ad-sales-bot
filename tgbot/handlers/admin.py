import json
import logging
from pathlib import Path

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from aioredis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services import service, db_queries
from tgbot.services.datatypes import ChatData, Period, SendingData
from tgbot.services.db_queries import get_chats, delete_chat, add_message, add_user, get_message
from tgbot.models.tables import Sending
from tgbot.keyboards import kb_admin, kb_user


def _check_msg_price(msg_text: str) -> int | None:
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
    amount = _check_msg_price(msg.text)
    if not amount:
        await msg.answer("Ответ должен быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.amount_posts = amount
    await state.update_data(chat_data=chat_data)
    await msg.answer("Введите цену за месяц")
    await state.set_state("price_month")


async def price_month(msg: Message, state: FSMContext):
    price = _check_msg_price(msg.text)
    if not price:
        await msg.answer("Цена должна быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.price_month = price
    await state.update_data(chat_data=chat_data)
    await msg.answer("Введите цену за 3 месяца")
    await state.set_state("price_3_month")


async def price_three_month(msg: Message, state: FSMContext):
    price = _check_msg_price(msg.text)
    if not price:
        await msg.answer("Цена должна быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.price_three_month = price
    await state.update_data(chat_data=chat_data)
    await msg.answer(f"Введите цену за неделю")
    await state.set_state("price_week")


async def price_week(msg: Message, db, state: FSMContext):
    price = _check_msg_price(msg.text)
    if not price:
        await msg.answer("Цена должна быть числом")
        return
    chat_data: ChatData = (await state.get_data()).get("chat_data")
    chat_data.price_week = price
    await service.add_chat(db, chat_data)
    await msg.answer("Готово")
    await state.finish()


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
    await state.update_data(chats=chats)
    await msg.answer("Выберите чат", reply_markup=kb)
    await state.set_state("select_chat_for_update")


async def select_chat_for_update(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    current_chat = list(filter(lambda chat: chat.chat_id == call.data, data["chats"]))[0]
    chat_data = ChatData()
    chat_data.chat_id = call.data
    await state.update_data(chat_data=chat_data)
    amount_members = await call.bot.get_chat_members_count(call.data)
    await call.message.answer(
        f"<b>Текущие данные</b>\nКоличество постов: {current_chat.amount_posts}\n"
        f"Цена за неделю: {current_chat.price_week}\n"
        f"Цена за месяц: {current_chat.price_month}\nЦена за 3 месяца: {current_chat.price_three_month}"
    )
    await call.message.answer(
        f"Количество участников в группе - {amount_members}. Через какое количество постов должна появляться реклама?"
    )
    await state.set_state("get_amount_posts")


async def cmd_update_start_message(msg: Message, state: FSMContext):
    await msg.answer("Введите сообщение")
    await state.set_state("get_text_for_start_message")


async def get_text_for_start_message(msg: Message, db, state: FSMContext):
    await add_message(db, "start", msg.text)
    await msg.answer("Готово")
    await state.finish()


async def cmd_get_promo_code(msg: Message, state: FSMContext):
    kb = kb_user.select_buy_period(True)
    await msg.answer("Выберите период", reply_markup=kb)
    await state.set_state("select_period_for_promo_code")
    # promo_code = service.generate_promo_code(8)
    # await msg.answer(promo_code)
    # await add_message(db, "promo_code", promo_code)


async def btn_select_period_for_promo_code(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    await call.answer()
    promo_code = service.generate_promo_code(call.data, call.from_user.id)
    await call.message.answer(promo_code)
    await add_message(db, "promo_code", promo_code)
    await state.finish()


async def cmd_add_group_user(msg: Message, state: FSMContext):
    await msg.answer("Отправьте файл с ID пользователей")
    await state.set_state("get_file_group_user")


async def get_file_with_group_user(msg: Message, db: AsyncSession, state: FSMContext):
    file = await msg.document.download()
    with open(file.name) as file:
        for line in file:
            try:
                user_id = int(line.strip())
            except ValueError:
                logging.error("Один из id был не числом")
                continue
            await db_queries.add_group_user(db, user_id, True)
    await state.finish()
    await msg.answer("Готово")
    Path(file.name).unlink()


async def cmd_delete_my_ads(msg: Message, db: AsyncSession, state: FSMContext):
    ads = await db_queries.get_sending_list(db)
    messages = []
    for price, ad in ads.items():
        kb = kb_admin.select_sending(price)
        text_chats = "\n    -".join([chat.name for chat in ad.chats])
        promo_code_text = f"Промокод оформил: {ad.who_gave_promo_code}" if ad.who_gave_promo_code else ""
        sent_msg = await msg.answer(
            f"Дата покупки: {ad.created}\nСрок рекламы: {ad.expiration}\n"
            f"Название кнопки: {ad.button_title}\nСсылка: {ad.button_link}\nМетод оплаты: {ad.currency}\n"
            f"Цена: {ad.price}\nЦена в USD: {ad.price_in_usd}\nПользователь: {ad.user_id}\nЧаты:\n    -{text_chats}\n{promo_code_text}",
            reply_markup=kb, disable_web_page_preview=True
        )
        messages.append(sent_msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state("select_ad_for_delete")


async def btn_select_ad_for_delete(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    await db_queries.delete_sending(db, call.data.split(":")[-1])
    data = await state.get_data()
    for message in data["messages"]:
        await call.bot.delete_message(call.from_user.id, int(message))
    await call.message.answer("Готово")
    await state.finish()


async def btn_select_ad_for_change(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    sending = await db_queries.get_sending_by_price(db, call.data.split(":")[-1])
    kb = kb_admin.select_title_or_link_for_change()
    await state.update_data(sending=sending)
    await call.message.answer("Что изменить?", reply_markup=kb)
    await state.set_state("select_title_or_link")


async def btn_select_title_or_link(call: CallbackQuery, state: FSMContext):
    message = {"title": "новое название", "link": "новую ссылку"}
    await call.message.answer(f"Введите {message[call.data]}")
    await state.update_data(who_change=call.data)
    await state.set_state("new_title_or_link")


async def get_new_title_or_link(msg: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    if data["who_change"] == "title":
        await db_queries.update_sending(db, data["sending"].price, {"button_title": msg.text})
    else:
        await db_queries.update_sending(db, data["sending"].price, {"button_link": msg.text})
    await msg.answer("Готово")
    await state.finish()


async def btn_change_chats(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    sending: Sending = data["sending"]
    all_chats = await db_queries.get_chats(db)
    selected_chats = await db_queries.get_all_sending_by_price(db, sending.price)
    selected_chats = [sending.chat for sending in selected_chats]
    kb = kb_user.select_chat_for_buy(all_chats, Period.month, selected_chats)
    await state.set_state("select_chat_for_change")
    await call.message.answer("Выберите чаты", reply_markup=kb)
    await state.update_data(chats=all_chats, select_chats=selected_chats, tmp_price=0, period=Period.week)
    await call.message.answer('После завершения выбора нажмите "Завершить выбор"', reply_markup=kb_user.end_select_chat)


async def select_chats(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    select_chats = data["select_chats"]
    chat_id, price = call.data.split(":")
    if chat_id in select_chats:
        select_chats.remove(chat_id)
        data["tmp_price"] -= int(price)
    else:
        select_chats.append(chat_id)
        data["tmp_price"] += int(price)
    await state.update_data({"select_chats": select_chats, "tmp_price": data["tmp_price"]})
    kb = kb_user.select_chat_for_buy(data["chats"], data["period"], select_chats)
    await call.message.edit_reply_markup(reply_markup=kb)


async def btn_end_select_chat(msg: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    chats = data["select_chats"]
    sending: Sending = data["sending"]
    sending_data = SendingData(
        period=Period.week,
        chats=chats,
        btn_title=sending.button_title,
        btn_link=sending.button_link,
        price_in_usd=sending.price_in_usd,
        currency=sending.currency,
        who_gave_promo_code=sending.who_gave_promo_code
    )
    await db_queries.delete_sending(db, sending.price)
    await db_queries.add_sendings(db, sending_data, sending.price, msg.from_user.id, True)
    await state.finish()
    await msg.answer("Готово")


async def cmd_forbidden_words(msg: Message, state: FSMContext):
    await msg.answer("Отправьте файл со словами")
    await state.set_state("get_file_with_words")


async def get_file_with_words(msg: Message, state: FSMContext):
    redis: Redis = msg.bot.get("redis")
    file_with_words = await msg.document.download()
    words = []
    with open(file_with_words.name) as file:
        for line in file:
            words.append(line.strip().lower())
    await redis.delete("forbidden_words")
    await redis.lpush("forbidden_words", *words)
    with open("documents/forbidden_words.json", "w") as file:
        json.dump({"words": words}, file, indent=4, ensure_ascii=False)
    await msg.answer("Готово")
    await state.finish()
    Path(file_with_words.name).unlink()


async def cmd_change_ads_message(msg: Message, state: FSMContext):
    await msg.answer("Введите сообщение")
    await state.set_state("get_ads_message")


async def get_ads_message(msg: Message, db: AsyncSession, state: FSMContext):
    await db_queries.add_message(db, "ads_message", msg.text)
    await msg.answer("Готово")
    await state.finish()


async def cmd_set_partners(msg: Message, state: FSMContext):
    await msg.answer("Введите текст")
    await state.set_state("get_partners_text")


async def get_partners_text(msg: Message, db: AsyncSession, state: FSMContext):
    await db_queries.add_message(db, "partners", msg.text)
    await state.finish()
    await msg.answer("Готово")


def register_admin(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*", is_private=True)
    dp.register_message_handler(user_start, text="В начало", state="*", is_private=True)
    dp.register_message_handler(cmd_add_chat, commands=["add_chat"], state="*", is_admin=True)
    dp.register_message_handler(cmd_delete_chat, commands=["delete_chat"], state="*", is_admin=True)
    dp.register_message_handler(update_chat, commands=["edit_chat"], state="*", is_admin=True)
    dp.register_message_handler(cmd_update_start_message, commands=["update_start_message"], state="*", is_admin=True)
    dp.register_message_handler(cmd_get_promo_code, commands=["get_promo_code"], state="*", is_admin=True)
    dp.register_message_handler(cmd_add_group_user, commands=["add_group_user"], state="*", is_admin=True)
    dp.register_message_handler(cmd_delete_my_ads, commands=["delete_ads"], state="*", is_admin=True)
    dp.register_message_handler(cmd_forbidden_words, commands=["send_forbidden_words"], state="*", is_admin=True)
    dp.register_message_handler(cmd_change_ads_message, commands=["ads_message"], state="*", is_admin=True)
    dp.register_message_handler(cmd_set_partners, commands=["set_partners"], is_admin=True)
    dp.register_message_handler(get_partners_text, state="get_partners_text")
    dp.register_callback_query_handler(btn_add_chat, lambda call: call.data.startswith("add"))
    dp.register_message_handler(get_amount_posts, state="get_amount_posts")
    dp.register_message_handler(price_month, state="price_month")
    dp.register_message_handler(price_three_month, state="price_3_month")
    dp.register_message_handler(price_week, state="price_week")
    dp.register_callback_query_handler(select_group_for_delete, state="select_chat_for_delete")
    dp.register_callback_query_handler(select_chat_for_update, state="select_chat_for_update")
    dp.register_message_handler(get_text_for_start_message, state="get_text_for_start_message")
    dp.register_callback_query_handler(btn_select_period_for_promo_code, state="select_period_for_promo_code")
    dp.register_message_handler(get_file_with_group_user, state="get_file_group_user",
                                content_types=ContentType.DOCUMENT)
    dp.register_callback_query_handler(btn_select_ad_for_delete, text_contains="del", state="select_ad_for_delete")
    dp.register_callback_query_handler(btn_select_ad_for_change, text_contains="ch", state="select_ad_for_delete")
    dp.register_callback_query_handler(btn_change_chats, text="chats", state="select_title_or_link")
    dp.register_callback_query_handler(btn_select_title_or_link, state="select_title_or_link")
    dp.register_callback_query_handler(select_chats, state="select_chat_for_change")
    dp.register_message_handler(btn_end_select_chat, text="Завершить выбор", state="select_chat_for_change")
    dp.register_message_handler(get_new_title_or_link, state="new_title_or_link")
    dp.register_message_handler(get_file_with_words, state="get_file_with_words", content_types=ContentType.DOCUMENT)
    dp.register_message_handler(get_ads_message, state="get_ads_message")
