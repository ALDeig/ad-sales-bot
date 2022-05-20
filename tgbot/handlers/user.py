from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards import kb_user, kb_payments
from tgbot.services import db_queries
from tgbot.services import service
from tgbot.services.datatypes import Period, SendingData


async def user_start(msg: Message, db: AsyncSession, state: FSMContext):
    await state.finish()
    await db_queries.add_user(db, msg.from_user.id, msg.from_user.username)
    start_message = await db_queries.get_message(db, "start")
    kb = kb_user.buy_ad()
    await msg.answer(start_message.message if start_message else "Стартовое сообщение", reply_markup=kb)


async def btn_buy_ad(call: CallbackQuery, state: FSMContext):
    await call.answer()
    kb = kb_user.select_buy_period()
    await call.message.answer("Выберите период", reply_markup=kb)
    await call.message.answer('Для отмены нажмите "Назад"', reply_markup=kb_user.cancel)
    await state.set_state("select_period")


async def select_period(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    periods = {"7": Period.week, "30": Period.month, "90": Period.three_month}
    await call.answer()
    chats = await db_queries.get_chats(db)
    kb = kb_user.select_chat_for_buy(chats, periods[call.data])
    await state.set_state("select_chat")
    await call.message.answer("Выберите чаты", reply_markup=kb)
    message = await call.message.answer("Сумма к оплате: 0 USD")
    await state.update_data(
        period=periods[call.data], chats=chats, select_chats=[], tmp_price=0,
        id_msg_with_sum=message.message_id
    )
    await call.message.answer('После завершения выбора нажмите "Завершить выбор"', reply_markup=kb_user.end_select_chat)


async def select_chat(call: CallbackQuery, state: FSMContext):
    await call.answer()
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
    await call.bot.edit_message_text(
        text=f"Сумма к оплате: {data['tmp_price']} USD",
        chat_id=call.from_user.id,
        message_id=data["id_msg_with_sum"]
    )


async def end_select_chat(msg: Message, db: AsyncSession, state: FSMContext):
    await msg.answer("Готово", reply_markup=kb_user.cancel)
    data = await state.get_data()
    if not data["select_chats"]:
        await msg.answer("Вы не выбрил ни одного чата. Продолжите выбор или нажмите /start",
                         reply_markup=kb_user.end_select_chat)
        return
    config = msg.bot.get("config")
    sending_data = SendingData(period=data["period"], chats=data["select_chats"])
    prices = await service.get_prices(db, sending_data, config.pay.alpha_vantage_key)
    await state.update_data(sending_data=sending_data, prices=prices)
    text = "Введите рекламную ссылку. Ссылка должна начинаться с 'https://'" if "is_paid" in data else \
        f"Стоимость:\nUSD: {prices.usd}\nBTC: {prices.btc}\nLTC: {prices.ltc}\nDASH: {prices.dash}.\n\n" \
        f"Введите рекламную ссылку. Ссылка должна начинаться с 'https://'"
    await msg.answer(text, reply_markup=kb_user.cancel)
    await state.set_state("get_button_link")


async def get_button_link(msg: Message, state: FSMContext):
    if not msg.text.startswith("https://"):
        await msg.answer("Ссылка должна начинаться с 'https://'")
        return
    data = await state.get_data()
    data["sending_data"].btn_link = msg.text
    await state.update_data(sending_data=data["sending_data"])
    await msg.answer("Введите текст кнопки. Не больше 35 символов", reply_markup=kb_user.cancel)
    await state.set_state("get_button_title")


async def get_button_title(msg: Message, state: FSMContext):
    if len(msg.text) > 35:
        await msg.answer("Текст кнопки должен быть не больше 35 символов. Введите еще раз")
        return
    data = await state.get_data()
    sending_data = data["sending_data"]
    sending_data.btn_title = msg.text
    await state.update_data(sending_data=sending_data)
    kb = kb_payments.choose_currency()
    name_chats = "\n✔ ".join(chat.name for chat in data['chats'] if chat.chat_id in sending_data.chats)
    await msg.answer(
        text=f"Данные покупки:\nТекст кнопки: {sending_data.btn_title}\nСсылка: {sending_data.btn_link}\n"
             f"Чаты:\n✔ {name_chats}",
        reply_markup=kb_user.cancel
    )
    await msg.answer("Выберите валюту оплаты", reply_markup=kb)
    await state.set_state("choose_currency")


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*", is_private=True)
    dp.register_message_handler(user_start, text="Назад", state="*", is_private=True)
    dp.register_callback_query_handler(btn_buy_ad, lambda call: call.data == "buy_ad")
    dp.register_callback_query_handler(select_period, state="select_period")
    dp.register_callback_query_handler(select_chat, state="select_chat")
    dp.register_message_handler(end_select_chat, text="Завершить выбор", state="select_chat")
    dp.register_message_handler(get_button_link, state="get_button_link")
    dp.register_message_handler(get_button_title, state="get_button_title")

