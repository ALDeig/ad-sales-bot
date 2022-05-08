from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards import kb_user
from tgbot.services import db_queries
from tgbot.services import service
from tgbot.services.datatypes import Period


async def btn_promo_code(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите промокод")
    await state.set_state("get_promo_code")


async def get_promo_code(msg: Message, db: AsyncSession, state: FSMContext):
    check_promo_code = await service.check_promo_code(db, msg.text)
    if not check_promo_code:
        await msg.answer("Неверный код")
        return
    chats = await db_queries.get_chats(db)
    kb = kb_user.select_chat_for_buy(chats)
    await state.update_data(period=Period.week, chats=chats, select_chats=[], is_paid=True)
    await state.set_state("select_chat")
    await msg.answer("Выберите чаты", reply_markup=kb)
    await msg.answer('После завершения выбора нажмите "Завершить выбор"', reply_markup=kb_user.end_select_chat)


def registry_handler_promo_code(dp: Dispatcher):
    dp.register_callback_query_handler(btn_promo_code, state="select_period", text="promo_code")
    dp.register_message_handler(get_promo_code, state="get_promo_code")
