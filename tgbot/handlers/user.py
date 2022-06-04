from aiogram import Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards import kb_user, kb_payments
from tgbot.services import db_queries
from tgbot.services import service
from tgbot.services.datatypes import Period, SendingData


async def user_start(msg: Message, db: AsyncSession, state: FSMContext):  # handler
    await state.finish()
    await db_queries.add_user(db, msg.from_user.id, msg.from_user.username)
    start_message = await db_queries.get_message(db, "start")
    kb = kb_user.buy_ad()
    await msg.answer(start_message.message if start_message else "Стартовое сообщение", disable_web_page_preview=True,
                     reply_markup=kb)


async def btn_buy_ad_func(message: Message, state: FSMContext):
    kb = kb_user.select_buy_period()
    await message.answer("Выберите период", reply_markup=kb)
    await message.answer('Для отмены нажмите "В начало"', reply_markup=kb_user.cancel)
    await state.set_state("select_period")


async def btn_buy_ad(call: CallbackQuery, state: FSMContext):  # handler
    await call.answer()
    await btn_buy_ad_func(call.message, state)
    # kb = kb_user.select_buy_period()
    # await call.message.answer("Выберите период", reply_markup=kb)
    # await call.message.answer('Для отмены нажмите "В начало"', reply_markup=kb_user.cancel)
    # await state.set_state("select_period")


async def select_chats_func(message: Message, db: AsyncSession, state: FSMContext, period=None):
    if period is None:
        data = await state.get_data()
        period = data["period"]
    chats = await db_queries.get_chats(db)
    kb = kb_user.select_chat_for_buy(chats, period)
    await state.set_state("select_chat")
    await message.answer("Выберите чаты", reply_markup=kb)
    message_with_price = await message.answer("Сумма к оплате: 0 USD")
    await state.update_data(
        period=period, chats=chats, select_chats=[], tmp_price=0,
        id_msg_with_sum=message_with_price.message_id
    )
    await message.answer('После завершения выбора нажмите "Завершить выбор"', reply_markup=kb_user.end_select_chat)


async def select_period(call: CallbackQuery, db: AsyncSession, state: FSMContext):  # handler
    await call.answer()
    periods = {"7": Period.week, "30": Period.month, "90": Period.three_month}
    await select_chats_func(call.message, db, state, periods[call.data])
    # chats = await db_queries.get_chats(db)
    # kb = kb_user.select_chat_for_buy(chats, periods[call.data])
    # await state.set_state("select_chat")
    # await call.message.answer("Выберите чаты", reply_markup=kb)
    # message = await call.message.answer("Сумма к оплате: 0 USD")
    # await state.update_data(
    #     period=periods[call.data], chats=chats, select_chats=[], tmp_price=0,
    #     id_msg_with_sum=message.message_id
    # )
    # await call.message.answer('После завершения выбора нажмите "Завершить выбор"', reply_markup=kb_user.end_select_chat)


async def select_chat_func(message: Message, bot: Bot, call_data: str, user_id: int, state: FSMContext):
    data = await state.get_data()
    select_chats = data["select_chats"]
    chat_id, price = call_data.split(":")
    if chat_id in select_chats:
        select_chats.remove(chat_id)
        data["tmp_price"] -= int(price)
    else:
        select_chats.append(chat_id)
        data["tmp_price"] += int(price)
    await state.update_data({"select_chats": select_chats, "tmp_price": data["tmp_price"]})
    kb = kb_user.select_chat_for_buy(data["chats"], data["period"], select_chats)
    await message.edit_reply_markup(reply_markup=kb)
    await bot.edit_message_text(
        text=f"Сумма к оплате: {data['tmp_price']} USD",
        chat_id=user_id,
        message_id=data["id_msg_with_sum"]
    )


async def select_chat(call: CallbackQuery, state: FSMContext):  # handler
    await call.answer()
    await select_chat_func(call.message, call.bot, call.data, call.from_user.id, state)
    # data = await state.get_data()
    # select_chats = data["select_chats"]
    # chat_id, price = call.data.split(":")
    # if chat_id in select_chats:
    #     select_chats.remove(chat_id)
    #     data["tmp_price"] -= int(price)
    # else:
    #     select_chats.append(chat_id)
    #     data["tmp_price"] += int(price)
    # await state.update_data({"select_chats": select_chats, "tmp_price": data["tmp_price"]})
    # kb = kb_user.select_chat_for_buy(data["chats"], data["period"], select_chats)
    # await call.message.edit_reply_markup(reply_markup=kb)
    # await call.bot.edit_message_text(
    #     text=f"Сумма к оплате: {data['tmp_price']} USD",
    #     chat_id=call.from_user.id,
    #     message_id=data["id_msg_with_sum"]
    # )


async def btn_back_after_selected_chat(msg: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    if data["select_chats"]:
        await select_chats_func(msg, db, state)
    else:
        await btn_buy_ad_func(msg, state)


async def step_get_button_link(msg: Message, db: AsyncSession, state: FSMContext, prices=None):
    data = await state.get_data()
    if prices is None:
        prices = data["prices"]
    text = "Введите рекламную ссылку. Ссылка должна начинаться с 'https://'" if "is_paid" in data else \
        f"Стоимость:\nUSD: {prices.usd}\nBTC: {prices.btc}\nLTC: {prices.ltc}\nDASH: {prices.dash}.\n\n" \
        f"Введите рекламную ссылку. Ссылка должна начинаться с 'https://'"
    await msg.answer(text, reply_markup=kb_user.cancel_back)
    await state.set_state("get_button_link")


async def end_select_chat(msg: Message, db: AsyncSession, state: FSMContext):  # handler
    await msg.answer("Готово", reply_markup=kb_user.cancel_back)
    data = await state.get_data()
    if not data["select_chats"]:
        await msg.answer("Вы не выбрали ни одного чата. Продолжите выбор или нажмите /start",
                         reply_markup=kb_user.end_select_chat)
        return
    config = msg.bot.get("config")
    sending_data = SendingData(period=data["period"], chats=data["select_chats"], price_in_usd=data["tmp_price"])
    prices = await service.get_prices(db, sending_data, config.pay.alpha_vantage_key)
    await state.update_data(sending_data=sending_data, prices=prices)
    await step_get_button_link(msg, db, state, prices)
    # text = "Введите рекламную ссылку. Ссылка должна начинаться с 'https://'" if "is_paid" in data else \
    #     f"Стоимость:\nUSD: {prices.usd}\nBTC: {prices.btc}\nLTC: {prices.ltc}\nDASH: {prices.dash}.\n\n" \
    #     f"Введите рекламную ссылку. Ссылка должна начинаться с 'https://'"
    # await msg.answer(text, reply_markup=kb_user.cancel_back)
    # await state.set_state("get_button_link")


async def get_button_link_func(msg: Message, db: AsyncSession, state: FSMContext):
    await msg.answer("Введите текст кнопки. Не больше 35 символов", reply_markup=kb_user.cancel_back)
    await state.set_state("get_button_title")


async def get_button_link(msg: Message, db: AsyncSession, state: FSMContext):  # handler
    # await get_button_link_func(msg, state)
    if not msg.text.startswith("https://"):
        await msg.answer("Ссылка должна начинаться с 'https://'")
        return
    data = await state.get_data()
    data["sending_data"].btn_link = msg.text
    await state.update_data(sending_data=data["sending_data"])
    await get_button_link_func(msg, db, state)
    # await msg.answer("Введите текст кнопки. Не больше 35 символов", reply_markup=kb_user.cancel)
    # await state.set_state("get_button_title")


async def get_button_title_func(msg: Message, db: AsyncSession, state: FSMContext, data: dict | None = None):
    if data is None:
        data = await state.get_data()
    sending_data = data["sending_data"]
    kb = kb_payments.choose_currency()
    name_chats = "\n✔ ".join(chat.name for chat in data['chats'] if chat.chat_id in sending_data.chats)
    await msg.answer(
        text=f"Данные покупки:\nТекст кнопки: {sending_data.btn_title}\nСсылка: {sending_data.btn_link}\n"
             f"Чаты:\n✔ {name_chats}",
        reply_markup=kb_user.cancel_back
    )
    await msg.answer("Выберите валюту оплаты", reply_markup=kb)
    await state.set_state("choose_currency")


async def get_button_title(msg: Message, db, state: FSMContext):  # handler
    # await get_button_title_func(msg, state)
    if len(msg.text) > 35:
        await msg.answer("Текст кнопки должен быть не больше 35 символов. Введите еще раз")
        return
    data = await state.get_data()
    sending_data = data["sending_data"]
    sending_data.btn_title = msg.text
    await state.update_data(sending_data=sending_data)
    await get_button_title_func(msg, db, state, data)
    # kb = kb_payments.choose_currency()
    # name_chats = "\n✔ ".join(chat.name for chat in data['chats'] if chat.chat_id in sending_data.chats)
    # await msg.answer(
    #     text=f"Данные покупки:\nТекст кнопки: {sending_data.btn_title}\nСсылка: {sending_data.btn_link}\n"
    #          f"Чаты:\n✔ {name_chats}",
    #     reply_markup=kb_user.cancel
    # )
    # await msg.answer("Выберите валюту оплаты", reply_markup=kb)
    # await state.set_state("choose_currency")


async def btn_back(msg: Message, db: AsyncSession, state: FSMContext):
    now_state = await state.get_state()
    functions = {
        "select_chat": btn_back_after_selected_chat,
        "get_button_link": select_chats_func,
        "get_button_title": step_get_button_link,
        "choose_currency": get_button_link_func
    }
    await functions[now_state](msg, db, state)


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*", is_private=True)
    dp.register_message_handler(user_start, text="В начало", state="*", is_private=True)
    dp.register_message_handler(btn_back, text="Назад", state="*", is_private=True)
    dp.register_callback_query_handler(btn_buy_ad, lambda call: call.data == "buy_ad")
    dp.register_callback_query_handler(select_period, state="select_period")
    # dp.message_handlers(select_period, text="Назад", state="select_period")
    dp.register_callback_query_handler(select_chat, state="select_chat")
    # dp.message_handlers(select_chat, text="Назад", state="select_chat")
    dp.register_message_handler(end_select_chat, text="Завершить выбор", state="select_chat")
    dp.register_message_handler(get_button_link, state="get_button_link")
    dp.register_message_handler(get_button_title, state="get_button_title")

