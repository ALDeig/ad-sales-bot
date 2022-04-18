from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ContentType, LabeledPrice, PreCheckoutQuery
from blockcypher import from_base_unit
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
    await state.set_state("select_period")


async def select_period(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    periods = {"7": Period.week, "30": Period.month, "90": Period.three_month}
    await call.answer()
    chats = await db_queries.get_chats(db)
    kb = kb_user.select_chat_for_buy(chats)
    await state.update_data(period=periods[call.data], chats=chats, select_chats=[])
    await state.set_state("select_chat")
    await call.message.answer("Выберите чаты", reply_markup=kb)
    await call.message.answer('После завершения выбора нажмите "Завершить выбор"', reply_markup=kb_user.end_select_chat)


async def select_chat(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    select_chats = data["select_chats"]
    if call.data in select_chats:
        select_chats.remove(call.data)
    else:
        select_chats.append(call.data)
    await state.update_data(select_chats=select_chats)
    kb = kb_user.select_chat_for_buy(data["chats"], select_chats)
    await call.message.edit_reply_markup(kb)


async def end_select_chat(msg: Message, db: AsyncSession, state: FSMContext):
    await msg.answer("Готово", reply_markup=ReplyKeyboardRemove())
    data = await state.get_data()
    sending_data = SendingData(period=data["period"], chats=data["select_chats"])
    price_in_usd, price_in_btc = await service.get_price(db, sending_data)
    await state.update_data(sending_data=sending_data, price=price_in_btc)
    await msg.answer(f"Стоимость: {price_in_btc} BTC, {price_in_usd} $. Введите рекламную ссылку")
    await state.set_state("get_button_link")


async def get_button_link(msg: Message, state: FSMContext):
    data = await state.get_data()
    data["sending_data"].btn_link = msg.text
    await state.update_data(sending_data=data["sending_data"])
    await msg.answer("Введите текст кнопки")
    await state.set_state("get_button_title")


async def get_button_title(msg: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    sending_data = data["sending_data"]
    price = data["price"]
    sending_data.btn_title = msg.text
    await db_queries.add_sendings(db, sending_data, str(price), msg.from_user.id)
    kb = kb_payments.buy_keyboard(price, sending_data.period.value)
    await msg.answer("Купите рассылки", reply_markup=kb)
    await state.reset_state(with_data=False)


# async def select_amount_posts(call: CallbackQuery, db: AsyncSession, state: FSMContext):
#     await call.answer()
#     data = await state.get_data()
#     sending_data = SendingData(period=data["period"], chats=data["select_chats"], amount_posts=int(call.data))
#     price = await service.get_price(db, sending_data)
#     btc_price = from_base_unit(price, "btc")
#     await state.update_data(sending_data=sending_data, price=btc_price)
#     await call.message.answer(f"Стоимость - {price}. Введите ваш пост")
#     await state.set_state("get_post")


# async def get_post_message(msg: Message, state: FSMContext):
#     data = await state.get_data()
#     config = msg.bot.get("config")
#     data["sending_data"].post_id = msg.message_id
#     await state.update_data(sending_data=data["sending_data"])
#     price = data["price"] * 100
#     await msg.bot.send_invoice(
#         chat_id=msg.from_user.id,
#         title="Покупка рекламных постов",
#         description=f"На {data['sending_data'].period.value} дней",
#         payload="asdfasfas",
#         provider_token=config.tg.provider_token,
#         currency="RUB",
#         prices=[LabeledPrice(label="Купить", amount=price)],
#         start_parameter="adsagggsdkdkk"
#     )
#
#
# async def process_pre_checkout_query(query: PreCheckoutQuery, db, state: FSMContext):
#     await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
#     await query.bot.send_message(query.from_user.id, "Спасибо за покупку. Ваши рассылки созданы")
#     data = await state.get_data()
#     await service.create_sending(db, query.bot, data["sending_data"], query.from_user.id)
#     await state.finish()


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(btn_buy_ad, lambda call: call.data == "buy_ad")
    dp.register_callback_query_handler(select_period, state="select_period")
    dp.register_callback_query_handler(select_chat, state="select_chat")
    dp.register_message_handler(end_select_chat, text="Завершить выбор", state="select_chat")
    dp.register_message_handler(get_button_link, state="get_button_link")
    dp.register_message_handler(get_button_title, state="get_button_title")
    # dp.register_callback_query_handler()
    # dp.register_callback_query_handler(select_amount_posts, state="select_amount_posts")
    # dp.register_message_handler(get_post_message, state="get_post", content_types=ContentType.ANY)
    # dp.register_pre_checkout_query_handler(process_pre_checkout_query, state="get_post")

