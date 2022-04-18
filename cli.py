import asyncio

from tgbot.config import Settings
from tgbot.models import tables
from tgbot.services import db_connection


settings = Settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.db.user}:{settings.db.password}@{settings.db.host}/{settings.db.name}"
engine = db_connection.create_engine(DATABASE_URL)


if __name__ == "__main__":
    asyncio.run(db_connection.init_models(engine))
