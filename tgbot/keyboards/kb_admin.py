from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.models.tables import Chat, Sending


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


def select_sending(price: str):
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(text="Изменить", callback_data=f"ch:{price}"),
        InlineKeyboardButton(text="Удалить", callback_data=f"del:{price}")
    )
    return kb


def select_title_or_link_for_change():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Название кнопки", callback_data="title"),
        InlineKeyboardButton(text="Ссылка", callback_data="link")
    )
    return kb
