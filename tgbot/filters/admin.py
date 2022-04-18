import typing

from aiogram.dispatcher.filters import BoundFilter


class AdminFilter(BoundFilter):
    key = "is_admin"

    def __init__(self, is_admin: typing.Optional[bool] = None):
        self.is_admin = is_admin

    async def check(self, obj):
        if self.is_admin is None:
            return True
        config = obj.bot.get("config")
        return obj.from_user.id in config.tg.admins


class GroupFilter(BoundFilter):
    key = "is_group"

    def __init__(self, is_group: bool | None = None):
        self.is_group = is_group

    async def check(self, obj):
        if self.is_group is None:
            return True
        return obj.chat.type in ("group", "supergroup")
