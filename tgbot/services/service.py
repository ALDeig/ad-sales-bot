import asyncio
import random
from decimal import Decimal
from uuid import uuid4

import httpx
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.tables import Chat, Sending
from tgbot.services.datatypes import ChatData, SendingData, Period
from tgbot.services import db_queries
# from tgbot.services.scheduler import scheduler


async def add_chat(db: AsyncSession, data: ChatData):
    """Добавление чата в базу. Если такой чат есть, то обновляются цены"""
    chat = await db_queries.get_chat(db, data.chat_id)
    if chat:
        await db_queries.update_chat(db, data)
    else:
        await db_queries.add_chat(db, data)
    return True


async def usd_in_btc(usd: Decimal) -> Decimal:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://blockchain.info/tobtc", params={"currency": "USD", "value": usd})
        return Decimal(response.text)


def get_random_change_price(btc_price: Decimal) -> Decimal:
    random_value = Decimal(f"0.00000{random.randint(5, 500)}")
    result = btc_price + random_value
    return result


async def get_price(session: AsyncSession, sending_data: SendingData) -> tuple:
    """Считает цену в долларах и btc. Возвращает кортеж с ценами"""
    price_in_usd = Decimal(0)
    for chat in sending_data.chats:
        data_chat = await db_queries.get_chat(session, chat)
        prices = {
            Period.week: data_chat.price_week, Period.month: data_chat.price_month,
            Period.three_month: data_chat.price_three_month
        }
        price_in_usd += prices[sending_data.period]
    tmp_price_in_btc = await usd_in_btc(price_in_usd)
    price_in_btc = get_random_change_price(tmp_price_in_btc)
    price_in_btc = round(price_in_btc, 8)
    return price_in_usd, price_in_btc


async def start_sending(bot: Bot, chats: list[str], post_id: int, from_chat_id: int):
    for chat in chats:
        try:
            await bot.copy_message(chat, from_chat_id, post_id)
        except Exception as er:
            print(er)


def calculate_interval(amount_posts: int) -> str:
    # intervals = {1: ((20, 35),), 2: ((20, 27), (27, 35)), 3: ((20, 25), (25, 30), (30, 35))}
    intervals = {1: ((9, 21),), 2: ((9, 16), (16, 21)), 3: ((9, 12), (12, 17), (17, 21))}
    interval_str = ""
    for interval in intervals[amount_posts]:
        interval_str += str(random.randint(interval[0], interval[1])) + ", "
    return interval_str[:-2]


async def save_sending(session: AsyncSession, bot: Bot, sending_data: SendingData, from_chat_id: int):
    # for chat in sending_data.chats:
    #     uuid = uuid4()
    #     await db_queries.add_sending(session, from_chat_id,)
    # interval = calculate_interval(sending_data.amount_posts)
    # print(interval)
    # scheduler = bot.get("scheduler")
    uuid = uuid4()
    # scheduler.add_job(start_sending, "cron", hour=interval, id=str(uuid), jitter=100,
    #                   args=[bot, sending_data.chats, sending_data.post_id, from_chat_id])
    await db_queries.add_sending(session, sending_data, from_chat_id, uuid)


async def update_sending(session: AsyncSession, bot: Bot, scheduler, sending: Sending):
    intervals = calculate_interval(sending.amount_posts)
    print(intervals)
    uuid = uuid4()
    scheduler.add_job(start_sending, "cron", hour=intervals, id=str(uuid), jitter=100,
                      args=[bot, sending.chats, sending.post_id, sending.user_id])
    await db_queries.update_sending(session, sending.id, uuid)


# async def main():
#     sending_data = SendingData(
#         period=Period.week,
#         chats=["123", "321"],
#         post_id=12324,
#         amount_posts=2
#     )
#     uuid = uuid4()
#     scheduler.start()
#     await create_sending("sdfa", "adsfs", sending_data, 12355)
#
#
# asyncio.run(main())