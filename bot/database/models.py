from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from bot.utils.time import utcnow


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    announcements: Mapped[list["Announcement"]] = relationship(back_populates="owner")
    chats: Mapped[list["Chat"]] = relationship(back_populates="owner")
    collections: Mapped[list["ChatCollection"]] = relationship(back_populates="owner")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="owner")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    route_from: Mapped[str | None] = mapped_column(String(120), nullable=True)
    route_to: Mapped[str | None] = mapped_column(String(120), nullable=True)
    departure_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    price: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    owner: Mapped["User"] = relationship(back_populates="announcements")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="announcement")


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = (UniqueConstraint("user_id", "chat_id", name="uq_user_chat"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str] = mapped_column(String(255))
    chat_type: Mapped[str] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    bot_is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    user_is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="chats")
    collection_links: Mapped[list["CollectionChat"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class ChatCollection(Base):
    __tablename__ = "chat_collections"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_collection_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="collections")
    chats: Mapped[list["CollectionChat"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="collection")


class CollectionChat(Base):
    __tablename__ = "collection_chats"
    __table_args__ = (UniqueConstraint("collection_id", "chat_id", name="uq_collection_chat"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("chat_collections.id", ondelete="CASCADE")
    )
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))

    collection: Mapped["ChatCollection"] = relationship(back_populates="chats")
    chat: Mapped["Chat"] = relationship(back_populates="collection_links")


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "announcement_id", "collection_id", name="uq_schedule_target"
        ),
        Index("ix_schedules_due", "is_active", "next_send_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    announcement_id: Mapped[int] = mapped_column(
        ForeignKey("announcements.id", ondelete="CASCADE")
    )
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("chat_collections.id", ondelete="CASCADE")
    )
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_send_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="schedules")
    announcement: Mapped["Announcement"] = relationship(back_populates="schedules")
    collection: Mapped["ChatCollection"] = relationship(back_populates="schedules")


class PostLog(Base):
    __tablename__ = "post_logs"
    __table_args__ = (Index("ix_post_logs_schedule", "schedule_id", "sent_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )
    chat_id: Mapped[int] = mapped_column(BigInteger)
    chat_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
