from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Period(Enum):
    week = 7
    month = 30
    three_month = 90


class Currencies(Enum):
    btc = "BTC"
    ltc = "LTC"
    dash = "DASH"


@dataclass
class Prices:
    usd: Decimal | None = None
    btc: Decimal | None = None
    ltc: Decimal | None = None
    dash: Decimal | None = None


@dataclass
class SendingData:
    period: Period | None = None
    chats: list[str] = None
    btn_title: str = None
    btn_link: str = None
    # post_id: int = None


@dataclass(init=True)
class ChatData:
    chat_id: str | None = None
    name: str | None = None
    price_month: int | None = None
    price_three_month: int | None = None
    price_week: int | None = None
    amount_posts: int | None = None


# from uuid import uuid4
# uuid = uuid4()
# print(uuid)