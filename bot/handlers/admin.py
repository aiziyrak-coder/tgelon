import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Config
from bot.database.db import Database
from bot.database import repository as repo
from bot.keyboards.inline import (
    CB_ADMIN,
    CB_ADMIN_BLOCK,
    CB_ADMIN_BROADCAST,
    CB_ADMIN_LOGS,
    CB_ADMIN_STATS,
    CB_ADMIN_UNBLOCK,
    CB_ADMIN_USER,
    CB_ADMIN_USERS,
    admin_menu_kb,
    admin_user_detail_kb,
    admin_users_kb,
)
from bot.keyboards.menus import cancel_kb, main_menu_kb
from bot.texts.uz import BTN_ADMIN
from bot.states import AdminStates
from bot.utils.html import esc
from bot.utils.time import format_local

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == BTN_ADMIN)
@router.message(F.text == "🛡 Admin panel")
async def admin_panel_msg(message: Message, is_super_admin: bool) -> None:
    if not is_super_admin:
        await message.answer("⛔ Ruxsat yo'q.")
        return
    await message.answer("🛡 <b>Admin panel</b>", reply_markup=admin_menu_kb())


@router.callback_query(F.data == CB_ADMIN)
async def admin_panel_cb(callback: CallbackQuery, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    await callback.message.edit_text("🛡 <b>Admin panel</b>", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == CB_ADMIN_STATS)
async def admin_stats(callback: CallbackQuery, db: Database, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    async with db.session_factory() as session:
        stats = await repo.get_stats(session)
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {stats['users']}\n"
        f"📢 E'lonlar: {stats['announcements']}\n"
        f"💬 Chatlar: {stats['chats']}\n"
        f"⏰ Rejalar: {stats['schedules']} (faol: {stats['active_schedules']})\n"
        f"📤 Jami yuborishlar: {stats['total_posts']}\n"
        f"✅ Muvaffaqiyat: {stats['success_rate']}%"
    )
    await callback.message.edit_text(text, reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith(CB_ADMIN_USERS))
async def admin_users_list(callback: CallbackQuery, db: Database, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    page = int(callback.data.split(":")[1]) if ":" in callback.data else 0
    async with db.session_factory() as session:
        users, total = await repo.list_users_page(session, page=page)
    await callback.message.edit_text(
        f"👥 <b>Foydalanuvchilar</b> ({total} ta)",
        reply_markup=admin_users_kb(users, page, total),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_ADMIN_USER}:"))
async def admin_user_detail(callback: CallbackQuery, db: Database, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    user_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        user = await repo.get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Topilmadi", show_alert=True)
        return
    status = "🚫 Bloklangan" if user.is_blocked else "✅ Faol"
    reg = "✅ Ha" if user.is_registered else "❌ Yo'q"
    text = (
        f"👤 <b>Foydalanuvchi</b>\n\n"
        f"ID: <code>{user.telegram_id}</code>\n"
        f"Ism: {esc(user.full_name or '—')}\n"
        f"Telefon: {esc(user.phone or '—')}\n"
        f"Username: @{user.username or '—'}\n"
        f"Holat: {status}\n"
        f"Ro'yxatdan o'tgan: {reg}\n"
        f"Qo'shilgan: {format_local(user.created_at)}"
    )
    await callback.message.edit_text(
        text, reply_markup=admin_user_detail_kb(user.id, user.is_blocked)
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_ADMIN_BLOCK}:"))
async def admin_block(callback: CallbackQuery, db: Database, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    user_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        await repo.set_user_blocked(session, user_id, True)
        user = await repo.get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    await callback.message.edit_reply_markup(
        reply_markup=admin_user_detail_kb(user.id, user.is_blocked)
    )
    await callback.answer("🚫 Bloklandi (rejalar to'xtatildi)")


@router.callback_query(F.data.startswith(f"{CB_ADMIN_UNBLOCK}:"))
async def admin_unblock(callback: CallbackQuery, db: Database, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    user_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        await repo.set_user_blocked(session, user_id, False)
        user = await repo.get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    await callback.message.edit_reply_markup(
        reply_markup=admin_user_detail_kb(user.id, user.is_blocked)
    )
    await callback.answer("✅ Blokdan chiqarildi")


@router.callback_query(F.data == CB_ADMIN_LOGS)
async def admin_logs(callback: CallbackQuery, db: Database, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    from sqlalchemy import select

    from bot.database.models import PostLog

    async with db.session_factory() as session:
        result = await session.execute(
            select(PostLog).order_by(PostLog.sent_at.desc()).limit(15)
        )
        logs = list(result.scalars().all())
    if not logs:
        text = "📜 Loglar yo'q."
    else:
        lines = ["📜 <b>So'nggi tizim loglari</b>\n"]
        for log in logs:
            icon = "✅" if log.success else "❌"
            title = log.chat_title or str(log.chat_id)
            lines.append(f"{icon} {esc(title)} — {format_local(log.sent_at)}")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == CB_ADMIN_BROADCAST)
async def admin_bc_start(callback: CallbackQuery, state: FSMContext, is_super_admin: bool) -> None:
    if not is_super_admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.answer("📣 Xabar matni:", reply_markup=cancel_kb())
    await callback.answer()


@router.message(AdminStates.waiting_broadcast, F.text == "❌ Bekor qilish")
async def admin_bc_cancel(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.message(AdminStates.waiting_broadcast, F.text)
async def admin_bc_send(
    message: Message,
    state: FSMContext,
    db: Database,
    bot: Bot,
    config: Config,
    is_super_admin: bool,
) -> None:
    if not is_super_admin:
        return
    await state.clear()
    async with db.session_factory() as session:
        users, _ = await repo.list_users_page(session, page=0, page_size=10000)
    sent = failed = 0
    progress = await message.answer("📣 Yuborilmoqda: 0%")
    total = len([u for u in users if not u.is_blocked])
    for i, user in enumerate(users):
        if user.is_blocked:
            continue
        try:
            await bot.send_message(
                user.telegram_id,
                f"📣 <b>Xabar admindan:</b>\n\n{esc(message.text)}",
            )
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 1)
            try:
                await bot.send_message(user.telegram_id, f"📣 <b>Xabar admindan:</b>\n\n{esc(message.text)}")
                sent += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1
        if total and (i + 1) % max(1, total // 10) == 0:
            pct = int((sent + failed) / total * 100)
            try:
                await progress.edit_text(f"📣 Yuborilmoqda: {pct}%")
            except Exception:
                pass
        await asyncio.sleep(config.broadcast_delay)
    await progress.edit_text(f"✅ Yuborildi: {sent}\n❌ Xato: {failed}")
    await message.answer("Tugadi.", reply_markup=main_menu_kb(is_admin=True))
