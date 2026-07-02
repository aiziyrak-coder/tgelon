"""Avtomatik yuborishni boshqarish (to'xtatish, vaqt o'zgartirish)."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.inline import (
    CB_SCHED_DELETE,
    CB_SCHED_DELETE_OK,
    CB_SCHED_EDIT_INT,
    CB_SCHED_TOGGLE,
    CB_SCHED_VIEW,
    active_schedules_kb,
    pick_interval_edit_kb,
    schedule_detail_kb,
)
from bot.keyboards.menus import cancel_kb, confirm_kb, main_menu_kb
from bot.states import ScheduleStates
from bot.texts.uz import BTN_CANCEL, BTN_HOME
from bot.utils.html import esc
from bot.utils.time import format_local

router = Router()


def _sched_text(sch) -> str:
    status = "✅ Ishlayapti" if sch.is_active else "⏸ To'xtatilgan"
    ann = sch.announcement.name if sch.announcement else "?"
    return (
        f"⏰ <b>Avtomatik yuborish</b>\n\n"
        f"Holat: {status}\n"
        f"📢 E'lon: {esc(ann)}\n"
        f"⏱ Har {sch.interval_minutes} daqiqada\n"
        f"📤 Oxirgi: {format_local(sch.last_sent_at)}\n"
        f"🔜 Keyingi: {format_local(sch.next_send_at)}"
    )


@router.callback_query(F.data.startswith(f"{CB_SCHED_VIEW}:"))
async def cb_sched_view(callback: CallbackQuery, db: Database, db_user: User) -> None:
    sched_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        sch = await repo.get_schedule(session, db_user.id, sched_id)
    if not sch:
        await callback.answer("Topilmadi", show_alert=True)
        return
    try:
        await callback.message.edit_text(_sched_text(sch), reply_markup=schedule_detail_kb(sch))
    except Exception:
        await callback.message.answer(_sched_text(sch), reply_markup=schedule_detail_kb(sch))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_SCHED_TOGGLE}:"))
async def cb_sched_toggle(
    callback: CallbackQuery, db: Database, db_user: User, is_super_admin: bool
) -> None:
    sched_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        await repo.toggle_schedule(session, db_user.id, sched_id)
        schedules = await repo.list_schedules(session, db_user.id)
        sch = await repo.get_schedule(session, db_user.id, sched_id)
    active = [s for s in schedules if s.is_active]
    if sch and sch.is_active:
        await callback.message.edit_text(
            _sched_text(sch), reply_markup=schedule_detail_kb(sch)
        )
    elif active:
        await callback.message.edit_text(
            f"⏰ <b>Avtomatik yuborish</b>\n\n✅ Ishlayapti: {len(active)} ta",
            reply_markup=active_schedules_kb(active),
        )
    else:
        await callback.message.edit_text(
            "⏸ Barcha avtomatik yuborish to'xtatildi.\n\n"
            "Qayta yoqish uchun «⏰ Avtomatik yuborish» tugmasini bosing.",
        )
        await callback.message.answer("Menyu:", reply_markup=main_menu_kb(is_admin=is_super_admin))
    await callback.answer("✅ Yangilandi")


@router.callback_query(F.data.regexp(r"^sched_edit_int:\d+$"))
async def cb_edit_int_menu(callback: CallbackQuery) -> None:
    sched_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=pick_interval_edit_kb(sched_id))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^sched_edit_int:\d+:\d+$"))
async def cb_edit_int_save(callback: CallbackQuery, db: Database, db_user: User) -> None:
    parts = callback.data.split(":")
    sched_id, minutes = int(parts[1]), int(parts[2])
    try:
        async with db.session_factory() as session:
            sch = await repo.update_schedule_interval(session, db_user.id, sched_id, minutes)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    if sch:
        await callback.message.edit_text(_sched_text(sch), reply_markup=schedule_detail_kb(sch))
        await callback.answer(f"✅ Endi har {minutes} daqiqada")
    else:
        await callback.answer("Xatolik", show_alert=True)


@router.callback_query(F.data.regexp(r"^sched_custom:\d+$"))
async def sched_custom_start(callback: CallbackQuery, state: FSMContext) -> None:
    sched_id = int(callback.data.split(":")[1])
    await state.set_state(ScheduleStates.waiting_edit_interval)
    await state.update_data(edit_sched_id=sched_id)
    await callback.message.answer(
        "✏️ Yangi interval (daqiqa, 1–10080):",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(ScheduleStates.waiting_edit_interval, F.text.in_([BTN_CANCEL, BTN_HOME]))
async def sched_custom_cancel(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.message(ScheduleStates.waiting_edit_interval, F.text)
async def sched_custom_save(
    message: Message, state: FSMContext, db: Database, db_user: User, is_super_admin: bool
) -> None:
    try:
        minutes = int(message.text.strip())
    except ValueError:
        await message.answer("Faqat raqam kiriting.", reply_markup=cancel_kb())
        return
    data = await state.get_data()
    sched_id = data.get("edit_sched_id")
    if not sched_id:
        await state.clear()
        return
    try:
        async with db.session_factory() as session:
            sch = await repo.update_schedule_interval(session, db_user.id, sched_id, minutes)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=cancel_kb())
        return
    await state.clear()
    if sch:
        await message.answer(
            f"✅ Endi har {minutes} daqiqada yuboriladi.",
            reply_markup=main_menu_kb(is_admin=is_super_admin),
        )
    else:
        await message.answer("Xatolik.", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.callback_query(F.data.startswith(f"{CB_SCHED_DELETE}:"))
async def cb_sched_del_ask(callback: CallbackQuery) -> None:
    sched_id = callback.data.split(":")[1]
    await callback.message.answer(
        "🗑 Avtomatik yuborishni o'chirasizmi?",
        reply_markup=confirm_kb(f"{CB_SCHED_DELETE_OK}:{sched_id}", f"{CB_SCHED_VIEW}:{sched_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_SCHED_DELETE_OK}:"))
async def cb_sched_delete(
    callback: CallbackQuery, db: Database, db_user: User, is_super_admin: bool
) -> None:
    sched_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ok = await repo.delete_schedule(session, db_user.id, sched_id)
        schedules = await repo.list_schedules(session, db_user.id)
    active = [s for s in schedules if s.is_active]
    if ok:
        if active:
            await callback.message.edit_text(
                f"🗑 O'chirildi.\n\nQolgan: {len(active)} ta",
                reply_markup=active_schedules_kb(active),
            )
        else:
            await callback.message.edit_text("🗑 O'chirildi. Avtomatik yuborish yo'q.")
            await callback.message.answer(
                "Menyu:", reply_markup=main_menu_kb(is_admin=is_super_admin)
            )
        await callback.answer()
    else:
        await callback.answer("Xatolik", show_alert=True)
