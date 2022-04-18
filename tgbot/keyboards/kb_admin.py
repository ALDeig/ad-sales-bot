from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.models.tables import Chat


def select_chat(chats: list[Chat]):
    """Клавиатура для выбора групп. Текст кнопок - username группы, callback_data - id группы"""
    kb = InlineKeyboardMarkup(row_width=1)
    for chat in chats:
        kb.add(
            InlineKeyboardButton(text=chat.name, callback_data=chat.chat_id)
        )
    return kb


def add_chat(chat_id: int | str):
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Добавить чат", callback_data=f"add:{chat_id}")
    )
    return kb
