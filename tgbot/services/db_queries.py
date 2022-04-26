from datetime import date, timedelta, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.dialects.postgresql import insert

from tgbot.models.tables import User, Sending, Message, Chat, GroupUser
from tgbot.services.datatypes import ChatData, SendingData


# Запросы для сообщений
async def get_message(session: AsyncSession, name: str) -> Message | None:
    """Получает сообщение по имени"""
    result = await session.execute(sa.select(Message).where(Message.name == name))
    return result.scalar()


async def add_message(session: AsyncSession, name: str, message_text: str) -> bool:
    """Запрос на добавление сообщения"""
    await session.execute(sa.delete(Message).where(Message.name == name))
    await session.commit()
    message = Message(name=name, message=message_text)
    session.add(message)
    try:
        await session.commit()
        return True
    except (IntegrityError, DBAPIError):
        await session.rollback()
        return False


async def delete_message(session: AsyncSession, name: str):
    await session.execute(sa.delete(Message).where(Message.name == name))
    await session.commit()


# Запросы для чатов
async def add_chat(session: AsyncSession, chat: ChatData):
    """Добавляет чат"""
    chat = Chat(
        chat_id=chat.chat_id,
        name=chat.name,
        amount_posts=chat.amount_posts,
        price_month=chat.price_month,
        price_three_month=chat.price_three_month,
        price_week=chat.price_week,
    )
    session.add(chat)
    await session.commit()


async def update_chat(session: AsyncSession, chat: ChatData):
    """Обновляет цены чата"""
    await session.execute(sa.update(Chat).where(Chat.chat_id == chat.chat_id).values(
        price_month=chat.price_month,
        price_three_month=chat.price_three_month,
        price_week=chat.price_week,
        amount_posts=chat.amount_posts
    ))
    await session.commit()


async def get_chats(session: AsyncSession) -> list[Chat]:
    """Возвращает все чаты из базы"""
    result = await session.execute(sa.select(Chat).order_by(Chat.name))
    return result.scalars().all()


async def get_chat(session: AsyncSession, chat_id: str) -> Chat | None:
    """Возвращает чат по id если он есть в базе"""
    result = await session.execute(sa.select(Chat).where(Chat.chat_id == chat_id))
    return result.scalar()


async def delete_chat(session: AsyncSession, chat_id: str):
    """Удаляет чат по id"""
    await session.execute(sa.delete(Chat).where(Chat.chat_id == chat_id))
    await session.commit()


async def add_sendings(session: AsyncSession, sending_data: SendingData, price: str, from_chat_id: int, is_paid=False):
    expiration = date.today() + timedelta(days=7) if is_paid else None
    for chat in sending_data.chats:
        sending = Sending(
            chat=chat,
            button_title=sending_data.btn_title,
            button_link=sending_data.btn_link,
            price=price,
            expiration=expiration,
            user_id=from_chat_id
        )
        session.add(sending)
    await session.commit()


async def update_expirations(session: AsyncSession, paid_period: int, price: str):
    await session.execute(sa.update(Sending).where(Sending.price == price).values(
        expiration=date.today() + timedelta(days=paid_period)
    ))
    await session.commit()


async def get_sendings(session: AsyncSession, chat_id: str) -> list[Sending]:
    # result = await session.execute(sa.select(Sending).where(Sending.chat == chat_id and Sending.expiration != None))
    result = await session.execute(sa.select(Sending).where(Sending.chat == chat_id, Sending.expiration.is_not(None)))
    return result.scalars().all()


async def delete_sending(session: AsyncSession, price: str):
    await session.execute(sa.delete(Sending).where(Sending.price == price))
    await session.commit()


async def delete_old_sending(session: AsyncSession):
    res = await session.execute(sa.delete(Sending).where(Sending.expiration < date.today()))
    await session.commit()
    # return res.scalars().all()


async def update_sending(session: AsyncSession, sending_id: UUID, job_id: UUID):
    await session.execute(sa.update(Sending).where(Sending.id == sending_id).values(job_id=job_id))
    await session.commit()


async def add_user(session: AsyncSession, user_id: int, username: str | None):
    insert_stmt = insert(User).values(id=user_id, username=username)
    do_nothing_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["id"])
    await session.execute(do_nothing_stmt)
    await session.commit()


async def add_group_user(session: AsyncSession, user_id: int, allow_ads: bool, check_time: datetime | None = None):
    if allow_ads:
        user = await get_group_user(session, user_id)
        if user:
            await update_group_user(session, user_id, {"allow_ads": True, "check_time": None})
            await session.commit()
            return
    session.add(
        GroupUser(
            user_id=user_id,
            allow_ads=allow_ads,
            check_time=check_time
        )
    )
    await session.commit()


async def get_group_user(session: AsyncSession, user_id: int) -> GroupUser | None:
    user = await session.execute(sa.select(GroupUser).where(GroupUser.user_id == user_id))
    return user.scalar()


async def delete_group_user(session: AsyncSession, check_time: datetime):
    await session.execute(sa.delete(GroupUser).where(GroupUser.check_time < check_time))
    await session.commit()


async def update_group_user(session: AsyncSession, user_id: int, update_field: dict):
    await session.execute(sa.update(GroupUser).where(GroupUser.user_id == user_id).values(**update_field))
    await session.commit()