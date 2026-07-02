from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated

from bot.database.db import Database
from bot.database import repository as repo
from bot.utils.chat_admin import is_admin_status

router = Router()

INACTIVE_STATUSES = {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.RESTRICTED}


@router.my_chat_member()
async def on_bot_chat_member(update: ChatMemberUpdated, db: Database, bot: Bot) -> None:
    chat = update.chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
        return

    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status
    actor = update.from_user
    if not actor:
        return

    title = chat.title or str(chat.id)
    chat_type = "channel" if chat.type == ChatType.CHANNEL else "group"
    bot_is_admin = is_admin_status(new_status)

    if new_status in INACTIVE_STATUSES:
        async with db.session_factory() as session:
            await repo.update_all_chats_by_telegram_id(
                session, chat.id, bot_is_admin=False, is_active=False, title=title
            )
        try:
            await bot.send_message(
                actor.id,
                f"❌ <b>{title}</b> — bot chiqarildi.\nE'lon tarqatish to'xtadi.",
            )
        except Exception:
            pass
        return

    if new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        user_is_admin = False
        try:
            actor_member = await bot.get_chat_member(chat.id, actor.id)
            user_is_admin = is_admin_status(actor_member.status)
        except Exception:
            pass

        async with db.session_factory() as session:
            user = await repo.get_or_create_user(
                session,
                telegram_id=actor.id,
                username=actor.username,
                full_name=actor.full_name,
            )
            db_chat = await repo.upsert_chat(
                session,
                user_id=user.id,
                chat_id=chat.id,
                title=title,
                chat_type=chat_type,
                bot_is_admin=bot_is_admin,
                user_is_admin=user_is_admin,
            )
            if bot_is_admin and user_is_admin:
                await repo.auto_add_chat_to_default(session, user.id, db_chat.id)

        if bot_is_admin and user_is_admin:
            note = (
                "✅ <b>Tayyor!</b> Guruh qo'shildi.\n\n"
                "«📡 E'lon tarqatish» — e'lon, jamlanma va vaqtni tanlang."
            )
        elif bot_is_admin and not user_is_admin:
            note = (
                "⚠️ Bot admin, lekin <b>siz admin emassiz</b>!\n\n"
                "E'lon tarqatish uchun <b>siz ham admin</b> bo'lishingiz kerak."
            )
        elif old_status and is_admin_status(old_status):
            note = "⚠️ Bot admin emas! E'lon ketmaydi. Qayta admin qiling."
        else:
            note = (
                "⚠️ Bot qo'shildi, lekin <b>ADMIN emas</b>!\n\n"
                "Botni admin qiling va «Xabar yuborish» huquqini bering."
            )

        try:
            await bot.send_message(actor.id, f"👥 <b>{title}</b>\n\n{note}")
        except Exception:
            pass
