from decimal import Decimal

from pydantic import BaseSettings

from tgbot.services.datatypes import Currencies


class DefaultConfig(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class TgBot(DefaultConfig):
    token: str
    admins: list[int]
    provider_token: str
    use_redis: bool


class BlockCypher(DefaultConfig):
    wallet_btc: str
    wallet_ltc: str
    wallet_dash: str
    blockcypher_token: str
    alpha_vantage_key: str


class DbConfig(DefaultConfig):
    password: str
    user: str
    name: str
    host: str = "127.0.0.1"

    class Config:
        env_prefix = "DB_"




class Settings(BaseSettings):
    tg: TgBot = TgBot()
    db: DbConfig = DbConfig()
    pay: BlockCypher = BlockCypher()
    # request_link: str = "bitcoin:{address}?" \
    #                     "amount={amount}" \
    #                     "&label={message}"
