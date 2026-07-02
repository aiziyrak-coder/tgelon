"""Guruh admin holatini yangilash."""
from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.database import repository as repo
from bot.database.db import Database
from bot.utils.chat_admin import is_admin_status

ADMIN_OK = {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}


async def refresh_user_chats(bot: Bot, db: Database, user_id: int, user_telegram_id: int) -> list:
    async with db.session_factory() as session:
        chats = await repo.list_chats(session, user_id)

    for c in chats:
        bot_admin = False
        user_admin = False
        try:
            bot_member = await bot.get_chat_member(c.chat_id, bot.id)
            bot_admin = is_admin_status(bot_member.status)
            user_member = await bot.get_chat_member(c.chat_id, user_telegram_id)
            user_admin = is_admin_status(user_member.status)
        except Exception:
            pass

        async with db.session_factory() as session:
            await repo.upsert_chat(
                session,
                user_id=user_id,
                chat_id=c.chat_id,
                title=c.title,
                chat_type=c.chat_type,
                bot_is_admin=bot_admin,
                user_is_admin=user_admin,
            )
            if bot_admin and user_admin:
                fresh = await repo.get_chat(session, user_id, c.id)
                if fresh:
                    await repo.auto_add_chat_to_default(session, user_id, fresh.id)

    async with db.session_factory() as session:
        return await repo.list_chats(session, user_id)
