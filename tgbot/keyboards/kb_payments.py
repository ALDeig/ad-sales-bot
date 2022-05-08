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


def paid_keyboard(price, currency):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=f"paid:{price}:{currency}"
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


def choose_currency():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="BTC", callback_data="btc")],
            [InlineKeyboardButton(text="Litecoin", callback_data="ltc")],
            [InlineKeyboardButton(text="Dash", callback_data="dash")]
        ]
    )
    return kb


def cancel_or_change_currency():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отменить", callback_data="true_cancel")],
            [InlineKeyboardButton(text="Изменить валюту", callback_data="change_currency")]
        ]
    )
    return kb