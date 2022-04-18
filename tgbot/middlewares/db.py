from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class DbMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["update"]

    async def pre_process(self, obj, data: dict, *args):
        session_factory = obj.bot.get("session_factory")
        session = session_factory()
        data["db"] = session

    async def post_process(self, obj, data: dict, *args):
        if data.get("db", None):
            session = data.get("db")
            await session.close()
