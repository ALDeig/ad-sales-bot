from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


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
    price_in_usd: int = None
    currency: str = None
    who_gave_promo_code: int = None
    # post_id: int = None


@dataclass(init=True)
class ChatData:
    chat_id: str | None = None
    name: str | None = None
    price_month: int | None = None
    price_three_month: int | None = None
    price_week: int | None = None
    amount_posts: int | None = None


class ChatInfo(BaseModel):
    id: str
    name: str


class SendingWithChats(BaseModel):
    button_link: str
    button_title: str
    price: str
    expiration: date
    created: date
    user_id: int
    price_in_usd: int
    currency: str
    who_gave_promo_code: int | None = None
    chats: list[ChatInfo] | None = None

    class Config:
        orm_mode=True


# from uuid import uuid4
# uuid = uuid4()
# print(uuid)