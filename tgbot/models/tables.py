import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from tgbot.services.db_connection import Base


class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.BigInteger(), primary_key=True, index=True)
    username = sa.Column(sa.String(), nullable=True)
    sending_id = relationship("Sending")


class Chat(Base):
    __tablename__ = "chats"
    chat_id = sa.Column(sa.String(), primary_key=True)
    name = sa.Column(sa.String(), nullable=True)
    username = sa.Column(sa.String())
    amount_posts = sa.Column(sa.Integer())
    price_month = sa.Column(sa.Integer())
    price_three_month = sa.Column(sa.Integer())
    price_week = sa.Column(sa.Integer())


class Sending(Base):
    __tablename__ = "sendings"
    id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    chat = sa.Column(sa.ForeignKey("chats.chat_id"))
    button_title = sa.Column(sa.String())
    button_link = sa.Column(sa.String())
    price = sa.Column(sa.String())
    expiration = sa.Column(sa.Date(), nullable=True)
    created = sa.Column(sa.Date(), server_default=sa.sql.func.now())
    user_id = sa.Column(sa.ForeignKey("users.id"))


class Message(Base):
    __tablename__ = "messages"
    name = sa.Column(sa.String(), primary_key=True)
    message = sa.Column(sa.Text(), default="Дефолтное сообщение")
