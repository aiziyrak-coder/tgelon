import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import Announcement, Chat, User
from bot.utils.chat_admin import is_admin_status
from bot.utils.html import esc
from bot.utils.post_body import build_post_text
from bot.utils.telegram import with_retry
from bot.utils.text import validate_message

logger = logging.getLogger(__name__)


def _phone_markup(phone: str | None) -> InlineKeyboardMarkup | None:
    if not phone:
        return None
    from bot.utils.phone import normalize_phone

    tel = normalize_phone(phone)
    if not tel:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Qo'ng'iroq qilish", url=f"tel:{tel}")]
        ]
    )


async def _verify_chat_access(
    bot: Bot, chat: Chat, owner: User
) -> tuple[bool, str | None]:
    try:
        bot_member = await bot.get_chat_member(chat.chat_id, bot.id)
        user_member = await bot.get_chat_member(chat.chat_id, owner.telegram_id)
    except Exception as exc:
        msg = str(exc)
        if "chat not found" in msg.lower() or "kicked" in msg.lower():
            return False, "Guruh topilmadi yoki bot chiqarilgan"
        return False, msg

    if not is_admin_status(bot_member.status):
        return False, "Bot admin emas"
    if not is_admin_status(user_member.status):
        return False, "Siz bu guruhda admin emassiz"
    return True, None


async def send_announcement_to_chat(
    bot: Bot, chat: Chat, announcement: Announcement, owner: User
) -> tuple[bool, str | None]:
    ok, err = await _verify_chat_access(bot, chat, owner)
    if not ok:
        return False, err

    post_text = build_post_text(announcement, owner)
    err = validate_message(post_text, has_photo=bool(announcement.photo_file_id))
    if err:
        return False, err

    markup = _phone_markup(announcement.phone or owner.phone)
    try:
        if announcement.photo_file_id:
            await with_retry(
                lambda: bot.send_photo(
                    chat_id=chat.chat_id,
                    photo=announcement.photo_file_id,
                    caption=post_text,
                    reply_markup=markup,
                )
            )
        else:
            await with_retry(
                lambda: bot.send_message(
                    chat_id=chat.chat_id,
                    text=post_text,
                    reply_markup=markup,
                )
            )
        return True, None
    except Exception as exc:
        msg = getattr(exc, "message", None) or str(exc)
        if "bot was kicked" in msg.lower() or "forbidden" in msg.lower():
            return False, "Botga ruxsat yo'q yoki guruhdan chiqarilgan"
        return False, msg


async def send_announcement_to_collection(
    bot: Bot,
    db: Database,
    user_id: int,
    announcement: Announcement,
    collection_id: int,
    owner: User,
    schedule_id: int | None = None,
    notify_user_id: int | None = None,
) -> dict:
    async with db.session_factory() as session:
        chats = await repo.get_collection_chats(session, user_id, collection_id)

    if not chats:
        return {
            "sent": 0,
            "failed": 0,
            "errors": ["Jamlanmada tayyor guruh yo'q (siz va bot admin bo'lishingiz kerak)"],
            "total": 0,
        }

    sent = 0
    failed = 0
    errors: list[str] = []
    log_entries: list[tuple[int, str | None, bool, str | None]] = []

    for chat in chats:
        ok, err = await send_announcement_to_chat(bot, chat, announcement, owner)
        log_entries.append((chat.chat_id, chat.title, ok, err))
        if ok:
            sent += 1
        else:
            failed += 1
            errors.append(f"{esc(chat.title)}: {esc(err or 'xato')}")

    async with db.session_factory() as session:
        await repo.log_posts_batch(session, user_id, schedule_id, log_entries)

    if notify_user_id and failed > 0:
        try:
            await bot.send_message(
                notify_user_id,
                f"⚠️ <b>Yuborishda xatolar</b>\n"
                f"✅ {sent} | ❌ {failed}\n\n" + "\n".join(errors[:8]),
            )
        except Exception:
            pass

    return {"sent": sent, "failed": failed, "errors": errors, "total": len(chats)}


async def process_due_schedules(bot: Bot, db: Database) -> None:
    async with db.session_factory() as session:
        schedules = await repo.get_due_schedules(session)

    for schedule in schedules:
        if not schedule.announcement or not schedule.announcement.is_active:
            async with db.session_factory() as session:
                await repo.mark_schedule_attempt(session, schedule.id, advance=False, pause=True)
            owner_tg_id = schedule.owner.telegram_id if schedule.owner else None
            if owner_tg_id:
                try:
                    await bot.send_message(
                        owner_tg_id,
                        "⏸ Tarqatish to'xtatildi — e'lon faol emas.",
                    )
                except Exception:
                    pass
            continue

        owner = schedule.owner
        if not owner:
            continue

        owner_tg_id = owner.telegram_id
        result = await send_announcement_to_collection(
            bot=bot,
            db=db,
            user_id=schedule.user_id,
            announcement=schedule.announcement,
            collection_id=schedule.collection_id,
            owner=owner,
            schedule_id=schedule.id,
            notify_user_id=owner_tg_id,
        )

        advance = result["sent"] > 0
        pause = False
        backoff = None
        if not advance:
            if result["total"] == 0:
                pause = True
            else:
                backoff = min(schedule.interval_minutes, 15)

        async with db.session_factory() as session:
            await repo.mark_schedule_attempt(
                session,
                schedule.id,
                advance=advance,
                pause=pause,
                backoff_minutes=backoff,
            )

        if pause and owner_tg_id:
            try:
                await bot.send_message(
                    owner_tg_id,
                    "⏸ Tarqatish to'xtatildi — jamlanmada tayyor guruh qolmadi.",
                )
            except Exception:
                pass

        logger.info(
            "Schedule %s: sent=%s failed=%s advance=%s pause=%s",
            schedule.id,
            result["sent"],
            result["failed"],
            advance,
            pause,
        )
