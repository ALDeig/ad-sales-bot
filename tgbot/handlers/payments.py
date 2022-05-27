import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards import kb_payments
from tgbot.services import db_queries
from tgbot.services.datatypes import Currencies
from tgbot.services.errors import NoPaymentFound
from tgbot.services.qr_code import qr_link
from tgbot.services.payments import Payment
from tgbot.services.service import create_link_for_qr_code, check_payment


async def get_selected_currency(call: types.CallbackQuery, db: AsyncSession, state: FSMContext):
    await call.answer(cache_time=20)
    data = await state.get_data()
    sending_data = data["sending_data"]
    currencies = {"btc": Currencies.btc, "ltc": Currencies.ltc, "dash": Currencies.dash}
    payment = Payment(data["prices"], data["sending_data"].period.value, currencies[call.data])
    sending_data.currency = call.data
    if data.get("is_paid", None):
        sending_data.who_gave_promo_code = int(data["who_gave_promo_code"])
        await db_queries.add_sendings(db, sending_data, str(payment.get_price_in_currency()),
                                      call.from_user.id, is_paid=True)
        await call.message.answer("Готово")
        await state.finish()
        return
    sending_data.price = payment.get_price_in_currency()
    await state.update_data(sending_data=sending_data)
    payment = Payment(data["prices"], data["sending_data"].period.value, currencies[call.data])
    # await state.update_data({"payment": payment, "sending_data": sending_data})
    # kb = kb_payments.buy_keyboard(sending_data.price, sending_data.period.value)
    # await call.message.answer("Купите рассылки", reply_markup=kb)
    # await state.reset_state(with_data=False)


# async def btn_buy(call: types.CallbackQuery, state: FSMContext):
#     await call.answer(cache_time=20)
#     data = await state.get_data()
#     payment = data["payment"]
    config = call.bot.get("config")
    wallets = {Currencies.btc: config.pay.wallet_btc, Currencies.ltc: config.pay.wallet_ltc,
               Currencies.dash: config.pay.wallet_dash}
    payment.create()
    # price = payment.get_price_in_currency()
    kb = kb_payments.paid_keyboard(sending_data.price, payment.currency)
    await call.message.answer(f"Оплатите {sending_data.price} {payment.currency.value} по адресу:\n" +
                              hcode(wallets[payment.currency]),
                              reply_markup=kb)
    qr_code = create_link_for_qr_code(sending_data.price, wallets[payment.currency], payment.currency)
    msg_photo = await call.message.answer_photo(photo=qr_link(qr_code))
    await state.set_state("pay")
    await state.update_data({"payment": payment, "msg_photo_id": msg_photo.message_id})


async def cancel_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    await call.bot.delete_message(call.from_user.id, data["msg_photo_id"])
    kb = kb_payments.cancel_or_change_currency()
    await call.message.edit_text("Отменить оплату или выбрать другую валюту?", reply_markup=kb)
    await state.set_state("cancel")


async def btn_change_currency(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    kb = kb_payments.choose_currency()
    await call.message.answer("Выберите валюту", reply_markup=kb)
    await state.set_state("choose_currency")


async def btn_true_cancel(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Готово")
    await state.finish()
    # price = call.data.split(":")[-1]
    # await db_queries.delete_sending(db, price)
    # await state.finish()


async def approve_payment(call: types.CallbackQuery, db: AsyncSession, state: FSMContext):
    await call.answer(cache_time=10)
    scheduler = call.bot.get("scheduler")
    data = await state.get_data()
    payment: Payment = data.get("payment")
    # logging.info(f"{payment=}")
    # logging.info(f"{data['sending_data']=}")
    await call.message.delete_reply_markup()
    await call.message.answer("Идет автоматическая проверка платежа, как только транзакция подтвердиться вам "
                              "придет уведомление")
    await state.finish()
    await check_payment(call, payment, data["sending_data"], db)
    # try:
    #     await payment.check_payment()
    # except NoPaymentFound:
    #     await call.message.answer("Транзакция не найдена.")
    #     return
    # else:
    #     await call.message.answer("Успешно оплачено")
    #     await db_queries.add_sendings(db, data["sending_data"], str(payment.get_price_in_currency()),
    #                                   call.from_user.id, True)
    # await call.message.delete_reply_markup()
    # await state.finish()


def register_payment(dp: Dispatcher):
    dp.register_callback_query_handler(btn_true_cancel, text="true_cancel", state="choose_currency")
    dp.register_callback_query_handler(get_selected_currency, state="choose_currency")
    # dp.register_callback_query_handler(btn_buy, text_contains="buy")
    dp.register_callback_query_handler(cancel_payment, text_contains="cancel", state="pay")
    dp.register_callback_query_handler(btn_true_cancel, text="true_cancel", state="cancel")
    dp.register_callback_query_handler(btn_change_currency, text="change_currency", state="cancel")
    dp.register_callback_query_handler(approve_payment, text_contains="paid", state="pay")
