import random
import re
from decimal import Decimal
from string import ascii_letters

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services import db_queries
from tgbot.services.datatypes import ChatData, SendingData, Period, Prices, Currencies


def generate_promo_code(len_code: int) -> str:
    """Генерирует новый промокод"""
    promo_code = "".join(random.choice(ascii_letters) for _ in range(len_code))
    return promo_code


async def check_promo_code(db: AsyncSession, promo_code: str) -> bool:
    """Проверяет промокод"""
    right_promo_code = await db_queries.get_message(db, "promo_code")
    if right_promo_code and promo_code == right_promo_code.message:
        await db_queries.delete_message(db, "promo_code")
        return True
    return False


async def add_chat(db: AsyncSession, data: ChatData):
    """Добавление чата в базу. Если такой чат есть, то обновляются цены"""
    chat = await db_queries.get_chat(db, data.chat_id)
    if chat:
        await db_queries.update_chat(db, data)
    else:
        await db_queries.add_chat(db, data)
    return True


async def usd_in_crypto_currency(usd_price: Decimal, currency: Currencies, api_key: str) -> Decimal:
    """Переводит цену в долларах в валюту из параметра currency"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.alphavantage.co/query", params={
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": currency.value,
            "to_currency": "USD",
            "apikey": api_key
        }, timeout=120)
        price = Decimal(response.json()["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        usd = 1 / price
        price = usd_price * usd
        return price.quantize(Decimal(".00000001"))


def get_random_change_price(price: Decimal) -> Decimal:
    """Добавляет к цене рандомное значение, чтобы цена была уникальной"""
    random_value = Decimal(f"0.00000{random.randint(5, 500)}")
    result = price + random_value
    return result


async def get_prices(session: AsyncSession, sending_data: SendingData, api_key) -> Prices:
    """Считает цену в долларах и других валютах. Возвращает dataclass со всеми ценами"""
    prices = Prices(usd=Decimal(0))
    for chat in sending_data.chats:
        data_chat = await db_queries.get_chat(session, chat)
        chat_prices = {
            Period.week: data_chat.price_week, Period.month: data_chat.price_month,
            Period.three_month: data_chat.price_three_month
        }
        prices.usd += chat_prices[sending_data.period]
    dict_prices = {}
    for currency in Currencies:
        tmp_price = await usd_in_crypto_currency(prices.usd, currency, api_key)
        price = get_random_change_price(tmp_price)
        # price = round(price, 8)
        dict_prices[currency] = price
    prices.btc = dict_prices[Currencies.btc]
    prices.ltc = dict_prices[Currencies.ltc]
    prices.dash = dict_prices[Currencies.dash]
    return prices


def check_forbidden_word_in_text(msg_text: str, forbidden_words: list) -> bool:
    """Проверяет есть ли в тексте ссылки, упоминания или слова из списка запрещенных"""
    pattern_text = r"http\S+|@\S+|@\s\S+"
    if forbidden_words:
        pattern_text += "|" + "|".join(forbidden_words)
    pattern = re.compile(pattern_text)
    text = msg_text.lower()
    result = re.search(pattern, text)
    return True if result else False


def create_link_for_qr_code(price: Decimal, address: str, currency: Currencies) -> str:
    """Формирует ссылку для qr-code"""
    names_currency = {Currencies.btc: "bitcoin", Currencies.ltc: "litecoin", Currencies.dash: "dash"}
    return f"{names_currency[currency]}:{address}?amount={price}&label=test"
