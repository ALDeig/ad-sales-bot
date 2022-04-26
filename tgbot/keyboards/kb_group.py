import random

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def emojis_kb(user_id) -> tuple[InlineKeyboardMarkup, str]:
    all_emojis = ["\U0001F4AF", "\U0001F98A", "\U0001F349", "\U0001F95D", "\U0001F3E1", "\U0001F3C0"]
    selected_emojis_for_keyboard = random.sample(all_emojis, 5)
    right_emoji = random.choice(selected_emojis_for_keyboard)
    kb = InlineKeyboardMarkup(row_width=5)
    for emoji in selected_emojis_for_keyboard:
        kb.insert(
                InlineKeyboardButton(text=emoji, callback_data="1" if emoji == right_emoji else "0")
        )
    return kb, right_emoji
