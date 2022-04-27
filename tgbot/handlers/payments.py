from decimal import Decimal

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services import db_queries
from tgbot.services.errors import NotConfirmed, NoPaymentFound
from tgbot.keyboards import kb_payments
from tgbot.services.payments import Payment
from tgbot.services.qr_code import qr_link


async def btn_buy(call: types.CallbackQuery, state: FSMContext):
    config = call.bot.get("config")
    _, price, period = call.data.split(":")
    payment = Payment(Decimal(price), int(period))
    payment.create()
    kb = kb_payments.paid_keyboard(str(price))
    await call.message.answer(f"Оплатите {price} BTC по адресу:\n" +
                              hcode(config.pay.wallet_btc),
                              reply_markup=kb)
    qr_code = config.request_link.format(address=config.pay.wallet_btc,
                                         amount=price,
                                         message="test")
    await call.message.answer_photo(photo=qr_link(qr_code))
    await state.set_state("btc")
    await state.update_data(payment=payment)


async def cancel_payment(call: types.CallbackQuery, db: AsyncSession, state: FSMContext):
    await call.message.edit_text("Отменено")
    price = call.data.split(":")[-1]
    await db_queries.delete_sending(db, price)
    await state.finish()


async def approve_payment(call: types.CallbackQuery, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    payment: Payment = data.get("payment")
    try:
        await payment.check_payment()
    except NotConfirmed:
        await call.message.answer("Транзакция найдена. Но еще не подтверждена. Попробуйте позже")
        return
    except NoPaymentFound:
        await call.message.answer("Транзакция не найдена.")
        return
    else:
        await call.message.answer("Успешно оплачено")
        await db_queries.update_expirations(db, payment.period, str(payment.amount))
    await call.message.delete_reply_markup()
    await state.finish()


def register_payment(dp: Dispatcher):
    dp.register_callback_query_handler(btn_buy, text_contains="buy")
    dp.register_callback_query_handler(cancel_payment, text_contains="cancel", state="btc")
    dp.register_callback_query_handler(approve_payment, text_contains="paid", state="btc")
