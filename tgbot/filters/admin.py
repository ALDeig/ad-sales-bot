import logging
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
        logging.info(obj.chat.type)
        return obj.chat.type in ("group", "supergroup")


class PrivateFilter(BoundFilter):
    key = "is_private"

    def __init__(self, is_private: bool | None = None):
        self.is_private = is_private

    async def check(self, obj):
        if self.is_private is None:
            return True
        return obj.chat.type == "private"
