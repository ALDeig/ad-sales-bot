from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.tables import Chat


def buy_ad():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Купить рекламу", callback_data="buy_ad")
    )
    return kb


def select_buy_period():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="30 дней", callback_data="30"),
        InlineKeyboardButton(text="90 дней", callback_data="90"),
        InlineKeyboardButton(text="7 дней", callback_data="7")
    )
    return kb


def select_chat_for_buy(chats: list[Chat], select_chat: list = None):
    if select_chat is None:
        select_chat = []
    select_icon = {"checked": "✔", "unchecked": "✖"}
    kb = InlineKeyboardMarkup(row_width=1)
    for chat in chats:
        icon = select_icon["checked"] if chat.chat_id in select_chat else select_icon["unchecked"]
        kb.add(
            InlineKeyboardButton(text=f"{icon} {chat.name}", callback_data=chat.chat_id)
        )
    return kb


end_select_chat = ReplyKeyboardMarkup([[KeyboardButton(text="Завершить выбор")]], resize_keyboard=True)


def select_amount_posts():
    kb = InlineKeyboardMarkup(row_width=3)
    for count in range(1, 4):
        kb.insert(InlineKeyboardButton(text=f"{str(count)} в день", callback_data=str(count)))
    return kb
