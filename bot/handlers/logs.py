"""Foydalanuvchi yuborish tarixi."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.inline import CB_LOGS, CB_MAIN
from bot.keyboards.menus import main_menu_kb
from bot.texts.uz import BTN_LOGS, HINT_LOGS
from bot.utils.html import esc
from bot.utils.time import format_local

router = Router()


def _format_logs(logs) -> str:
    if not logs:
        return "📜 <b>Yuborish tarixi bo'sh</b>\n\nHali e'lon yuborilmagan."
    lines = ["📜 <b>So'nggi yuborishlar</b>\n"]
    for log in logs:
        icon = "✅" if log.success else "❌"
        title = esc(log.chat_title or str(log.chat_id))
        when = format_local(log.sent_at)
        err = f" — {esc(log.error_message)}" if log.error_message and not log.success else ""
        lines.append(f"{icon} {when} | {title}{err}")
    return "\n".join(lines)


@router.message(F.text == BTN_LOGS)
async def logs_menu(message: Message, db: Database, db_user: User, is_super_admin: bool) -> None:
    async with db.session_factory() as session:
        logs = await repo.get_user_post_logs(session, db_user.id, limit=15)
    await message.answer(HINT_LOGS)
    await message.answer(
        _format_logs(logs),
        reply_markup=main_menu_kb(is_admin=is_super_admin),
    )


@router.callback_query(F.data == CB_LOGS)
async def cb_logs(callback: CallbackQuery, db: Database, db_user: User) -> None:
    async with db.session_factory() as session:
        logs = await repo.get_user_post_logs(session, db_user.id, limit=15)
    await callback.message.edit_text(_format_logs(logs))
    await callback.answer()
