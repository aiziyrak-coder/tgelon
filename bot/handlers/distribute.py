"""E'lon tarqatish: e'lon → jamlanma → vaqt → boshlash."""
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.database.repository import ScheduleExistsError
from bot.keyboards.inline import (
    CB_SCHED_TOGGLE,
    active_schedules_kb,
    dist_ann_list_kb,
    dist_collection_kb,
    dist_interval_kb,
)
from bot.keyboards.menus import main_menu_kb
from bot.services.poster import send_announcement_to_collection
from bot.texts.uz import BTN_DISTRIBUTE, HINT_DISTRIBUTE
from bot.utils.html import esc

router = Router()


async def _active_announcements(db: Database, user_id: int):
    async with db.session_factory() as session:
        anns = await repo.list_announcements(session, user_id)
    return [a for a in anns if a.is_active]


@router.message(F.text == BTN_DISTRIBUTE)
async def distribute_menu(
    message: Message, db: Database, db_user: User, is_super_admin: bool
) -> None:
    anns = await _active_announcements(db, db_user.id)
    async with db.session_factory() as session:
        schedules = await repo.list_schedules(session, db_user.id)
    active_sched = [s for s in schedules if s.is_active]

    if active_sched:
        lines = ["📡 <b>Faol tarqatishlar</b>\n"]
        for s in active_sched:
            ann = s.announcement.name if s.announcement else "?"
            col = s.collection.name if s.collection else "?"
            lines.append(f"• {esc(ann)} → {esc(col)} — har {s.interval_minutes} daq")
        lines.append("\n⏸ To'xtatish yoki yangi qo'shish:")
        await message.answer("\n".join(lines), reply_markup=active_schedules_kb(active_sched))

    if not anns:
        async with db.session_factory() as session:
            total = await repo.list_announcements(session, db_user.id)
        if not total:
            await message.answer(
                "📭 Avval «🚀 E'lon yaratish» orqali e'lon yarating.",
                reply_markup=main_menu_kb(is_admin=is_super_admin),
            )
            return
        await message.answer(
            "⏸ <b>Faol e'lon yo'q</b>\n\n"
            "«📋 Mening e'lonlarim» dan kerakli e'lonni <b>▶️ Yoqish</b> tugmasi bilan faollashtiring.",
            reply_markup=main_menu_kb(is_admin=is_super_admin),
        )
        return

    await message.answer(HINT_DISTRIBUTE)
    if len(anns) == 1:
        await _pick_collection(message, db, db_user, anns[0].id)
        return
    await message.answer(
        "1️⃣ <b>Qaysi e'lonni tarqatamiz?</b>",
        reply_markup=dist_ann_list_kb(anns),
    )


@router.callback_query(F.data == "dist_new")
async def dist_new(callback: CallbackQuery, db: Database, db_user: User) -> None:
    anns = await _active_announcements(db, db_user.id)
    if not anns:
        await callback.answer("Faol e'lon yo'q", show_alert=True)
        return
    await callback.message.edit_text(
        "1️⃣ Qaysi e'lonni tarqatamiz?",
        reply_markup=dist_ann_list_kb(anns),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^dist_ann:\d+$"))
async def dist_pick_ann(callback: CallbackQuery, db: Database, db_user: User) -> None:
    ann_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
    if not ann or not ann.is_active:
        await callback.answer("E'lon faol emas", show_alert=True)
        return
    await _pick_collection(callback.message, db, db_user, ann_id, edit=True)
    await callback.answer()


async def _pick_collection(
    target: Message, db: Database, db_user: User, ann_id: int, *, edit: bool = False
) -> None:
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
        cols = await repo.list_collections(session, db_user.id)
        counts = {
            c.id: await repo.count_ready_collection_chats(session, db_user.id, c.id)
            for c in cols
        }
    if not ann:
        return
    ready_cols = [c for c in cols if counts.get(c.id, 0) > 0]
    if not ready_cols:
        text = (
            f"❌ <b>{esc(ann.name)}</b> uchun tayyor jamlanma yo'q.\n\n"
            "Siz va bot <b>ikkilangiz ham admin</b> bo'lgan guruhlarni "
            "«📁 Jamlanmalar» ga qo'shing."
        )
        if edit:
            await target.edit_text(text)
        else:
            await target.answer(text, reply_markup=main_menu_kb())
        return
    text = (
        f"2️⃣ <b>Jamlanmani tanlang</b>\n\n"
        f"📢 E'lon: <b>{esc(ann.name)}</b>\n"
        f"<i>Faqat siz ham bot ham admin bo'lgan guruhlarga ketadi.</i>"
    )
    kb = dist_collection_kb(ann_id, ready_cols, counts)
    if edit:
        await target.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r"^dist_col:\d+:\d+$"))
async def dist_pick_col(callback: CallbackQuery, db: Database, db_user: User) -> None:
    parts = callback.data.split(":")
    ann_id, col_id = int(parts[1]), int(parts[2])
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
        col = await repo.get_collection(session, db_user.id, col_id)
        n = await repo.count_ready_collection_chats(session, db_user.id, col_id)
    if not ann or not col:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await callback.message.edit_text(
        f"3️⃣ <b>Vaqt oralig'ini tanlang</b>\n\n"
        f"📢 {esc(ann.name)}\n"
        f"📁 {esc(col.name)} ({n} ta guruh/kanal)\n\n"
        f"«▶️ Boshlash» — avtomatik tarqatishni yoqadi.",
        reply_markup=dist_interval_kb(ann_id, col_id),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^dist_start:\d+:\d+:\d+$"))
async def dist_start(
    callback: CallbackQuery,
    db: Database,
    db_user: User,
    bot: Bot,
    is_super_admin: bool,
) -> None:
    parts = callback.data.split(":")
    ann_id, col_id, minutes = int(parts[1]), int(parts[2]), int(parts[3])
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
        col = await repo.get_collection(session, db_user.id, col_id)
        user = await repo.get_user_by_id(session, db_user.id)
        try:
            sch = await repo.create_schedule(session, db_user.id, ann_id, col_id, minutes)
        except ScheduleExistsError:
            await callback.answer(
                "Bu e'lon va jamlanma uchun tarqatish allaqachon yoqilgan!",
                show_alert=True,
            )
            return
        except ValueError as exc:
            await callback.answer(str(exc), show_alert=True)
            return

    await callback.answer("📤 Birinchi e'lon yuborilmoqda...")
    result = await send_announcement_to_collection(
        bot, db, db_user.id, ann, col_id, user, schedule_id=sch.id, notify_user_id=db_user.telegram_id
    )

    if result["sent"] > 0:
        text = (
            f"✅ <b>Tarqatish boshlandi!</b>\n\n"
            f"📢 {esc(ann.name)}\n"
            f"📁 {esc(col.name)}\n"
            f"⏱ Har <b>{minutes}</b> daqiqada\n"
            f"📤 Hozir: {result['sent']} ta guruhga yuborildi"
        )
        if result["failed"]:
            text += f"\n❌ {result['failed']} tasida xato"
    else:
        text = (
            "❌ <b>Yuborilmadi</b>\n\n"
            "Siz va bot ikkalangiz ham admin bo'lgan guruh yo'q.\n"
            "«👥 Guruhlarim» va «📁 Jamlanmalar» ni tekshiring."
        )
        async with db.session_factory() as session:
            await repo.delete_schedule(session, db_user.id, sch.id)

    await callback.message.answer(text, reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.callback_query(F.data.regexp(r"^dist_once:\d+:\d+$"))
async def dist_once(
    callback: CallbackQuery,
    db: Database,
    db_user: User,
    bot: Bot,
    is_super_admin: bool,
) -> None:
    parts = callback.data.split(":")
    ann_id, col_id = int(parts[1]), int(parts[2])
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
        col = await repo.get_collection(session, db_user.id, col_id)
        user = await repo.get_user_by_id(session, db_user.id)

    if not ann or not col or not user:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await callback.answer("📤 Yuborilmoqda...")
    result = await send_announcement_to_collection(
        bot, db, db_user.id, ann, col_id, user, notify_user_id=db_user.telegram_id
    )

    if result["sent"] > 0:
        text = (
            f"✅ <b>Yuborildi!</b>\n\n"
            f"📤 {result['sent']} ta guruh/kanalga yetkazildi"
        )
        if result["failed"]:
            text += f"\n❌ {result['failed']} tasida xato"
    else:
        text = "❌ Yuborilmadi. Siz va bot admin bo'lgan guruh kerak."

    await callback.message.answer(text, reply_markup=main_menu_kb(is_admin=is_super_admin))
