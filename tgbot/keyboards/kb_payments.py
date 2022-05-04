from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def buy_keyboard(price, period):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Купить", callback_data=f"buy:{price}:{period}")
            ]
        ]
    )
    return keyboard


def paid_keyboard(price):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=f"paid:{price}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=f"cancel:{price}"
                )
            ],
        ]
    )
    return kb
