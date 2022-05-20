from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.tables import Chat
from tgbot.services.datatypes import Period


def buy_ad():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Купить рекламу", callback_data="buy_ad")
    )
    return kb


def select_buy_period():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="7 дней", callback_data="7"),
        InlineKeyboardButton(text="30 дней", callback_data="30"),
        InlineKeyboardButton(text="90 дней", callback_data="90"),
        InlineKeyboardButton(text="Ввести промокод", callback_data="promo_code")
    )
    return kb


def select_chat_for_buy(chats: list[Chat], period: Period, select_chat: list = None):
    if select_chat is None:
        select_chat = []
    select_icon = {"checked": "✔", "unchecked": "✖"}
    kb = InlineKeyboardMarkup(row_width=1)
    for chat in chats:
        chat_prices = {
            Period.week: chat.price_week, Period.month: chat.price_month,
            Period.three_month: chat.price_three_month
        }
        icon = select_icon["checked"] if chat.chat_id in select_chat else select_icon["unchecked"]
        kb.add(
            InlineKeyboardButton(
                text=f"{icon} {chat.name} / {chat_prices[period]} USD",
                callback_data=f"{chat.chat_id}:{chat_prices[period]}"
            )
        )
    return kb


end_select_chat = ReplyKeyboardMarkup([
    [KeyboardButton(text="Завершить выбор")],
    [KeyboardButton(text="Назад")]
],resize_keyboard=True)

cancel = ReplyKeyboardMarkup([[KeyboardButton(text="Назад")]], resize_keyboard=True)


def select_amount_posts():
    kb = InlineKeyboardMarkup(row_width=3)
    for count in range(1, 4):
        kb.insert(InlineKeyboardButton(text=f"{str(count)} в день", callback_data=str(count)))
    return kb
