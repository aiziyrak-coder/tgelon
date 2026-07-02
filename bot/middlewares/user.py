from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User as TgUser

from bot.config import Config
from bot.database.db import Database
from bot.database import repository as repo

BLOCKED_MSG = "🚫 Siz bloklangansiz. Admin bilan bog'laning."


def _extract_user(event: TelegramObject) -> TgUser | None:
    if isinstance(event, Update):
        if event.message and event.message.from_user:
            return event.message.from_user
        if event.edited_message and event.edited_message.from_user:
            return event.edited_message.from_user
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user
        if event.my_chat_member and event.my_chat_member.from_user:
            return event.my_chat_member.from_user
        return None
    if isinstance(event, (Message, CallbackQuery)):
        return event.from_user
    if hasattr(event, "from_user"):
        return event.from_user
    return None


class UserMiddleware(BaseMiddleware):
    def __init__(self, db: Database, config: Config) -> None:
        self.db = db
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = _extract_user(event)

        if not tg_user:
            data.setdefault("is_super_admin", False)
            return await handler(event, data)

        async with self.db.session_factory() as session:
            user = await repo.get_or_create_user(
                session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
            )

        is_admin = self.config.is_admin(tg_user.id)
        if user.is_blocked and not is_admin:
            msg = _extract_message(event)
            if msg:
                await msg.answer(BLOCKED_MSG)
            elif isinstance(event, CallbackQuery):
                await event.answer(BLOCKED_MSG, show_alert=True)
            return None

        data["db_user"] = user
        data["is_super_admin"] = is_admin
        return await handler(event, data)


def _extract_message(event: TelegramObject) -> Message | None:
    if isinstance(event, Update):
        return event.message or event.edited_message
    if isinstance(event, Message):
        return event
    if isinstance(event, CallbackQuery) and event.message:
        return event.message
    return None
