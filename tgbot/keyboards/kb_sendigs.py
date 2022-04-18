from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.models.tables import Sending


def kb_ads_buttons(sendings: list[Sending]):
    kb = InlineKeyboardMarkup(row_width=1)
    for sending in sendings:
        kb.add(
            InlineKeyboardButton(text=sending.button_title, url=sending.button_link)
        )
    return kb
