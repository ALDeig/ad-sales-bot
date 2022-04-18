from pydantic import BaseSettings


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
    blockcypher_token: str


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
    request_link: str = "bitcoin:{address}?" \
                        "amount={amount}" \
                        "&label={message}"
