"""E'lon tahrirlash va o'chirish — asosiy oqim guide.py da."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.inline import (
    CB_ANN_DELETE,
    CB_ANN_DELETE_OK,
    CB_ANN_EDIT_PHOTO,
    CB_ANN_EDIT_TEXT,
    CB_ANN_LIST,
    CB_ANN_TOGGLE,
    CB_ANN_VIEW,
    announcement_detail_kb,
    announcements_list_kb,
)
from bot.keyboards.menus import cancel_kb, confirm_kb, main_menu_kb
from bot.states import AnnouncementStates
from bot.texts.uz import BTN_CANCEL, BTN_HOME
from bot.utils.text import validate_message

router = Router()


@router.callback_query(F.data.startswith(f"{CB_ANN_EDIT_PHOTO}:"))
async def cb_ann_edit_photo(callback: CallbackQuery, state: FSMContext) -> None:
    ann_id = int(callback.data.split(":")[1])
    await state.set_state(AnnouncementStates.editing_photo)
    await state.update_data(ann_id=ann_id)
    await callback.message.answer("📷 Yangi rasm yuboring:", reply_markup=cancel_kb())
    await callback.answer()


@router.message(AnnouncementStates.editing_photo, F.text.in_([BTN_CANCEL, BTN_HOME]))
async def edit_photo_cancel(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.message(AnnouncementStates.editing_photo, F.photo)
async def ann_save_photo(
    message: Message, state: FSMContext, db: Database, db_user: User, is_super_admin: bool
) -> None:
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    async with db.session_factory() as session:
        ann = await repo.update_announcement(
            session, data["ann_id"], db_user.id, photo_file_id=photo_id
        )
    await state.clear()
    if ann:
        await message.answer("✅ Rasm yangilandi!", reply_markup=announcement_detail_kb(ann))
        await message.answer("Menyu:", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.callback_query(F.data.startswith(f"{CB_ANN_EDIT_TEXT}:"))
async def cb_ann_edit_text(callback: CallbackQuery, state: FSMContext) -> None:
    ann_id = int(callback.data.split(":")[1])
    await state.set_state(AnnouncementStates.editing_text)
    await state.update_data(ann_id=ann_id)
    await callback.message.answer(
        "✏️ Yangi matnni yozing:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(AnnouncementStates.editing_text, F.text.in_([BTN_CANCEL, BTN_HOME]))
async def edit_cancel(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.message(AnnouncementStates.editing_text, F.text)
async def ann_save_text(
    message: Message, state: FSMContext, db: Database, db_user: User, is_super_admin: bool
) -> None:
    err = validate_message(message.text)
    if err:
        await message.answer(err)
        return
    data = await state.get_data()
    async with db.session_factory() as session:
        ann = await repo.update_announcement(session, data["ann_id"], db_user.id, text=message.text)
    await state.clear()
    if ann:
        await message.answer(
            "✅ Matn yangilandi!",
            reply_markup=announcement_detail_kb(ann),
        )
        await message.answer("Menyu:", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.callback_query(F.data.startswith(f"{CB_ANN_TOGGLE}:"))
async def cb_ann_toggle(callback: CallbackQuery, db: Database, db_user: User) -> None:
    ann_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
        if ann:
            ann = await repo.update_announcement(
                session, ann_id, db_user.id, is_active=not ann.is_active
            )
    if ann:
        status = "yoqildi" if ann.is_active else "to'xtatildi"
        try:
            await callback.message.edit_reply_markup(reply_markup=announcement_detail_kb(ann))
        except Exception:
            pass
        await callback.answer(f"E'lon {status}")
    else:
        await callback.answer("Xatolik", show_alert=True)


@router.callback_query(F.data.startswith(f"{CB_ANN_DELETE}:"))
async def cb_ann_delete_ask(callback: CallbackQuery, db: Database, db_user: User) -> None:
    ann_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        sched_count = await repo.count_user_schedules_for_announcement(session, db_user.id, ann_id)
    warn = f"\n\n⚠️ {sched_count} ta avtomatik yuborish ham o'chadi!" if sched_count else ""
    await callback.message.answer(
        f"🗑 E'lonni o'chirasizmi?{warn}",
        reply_markup=confirm_kb(f"{CB_ANN_DELETE_OK}:{ann_id}", f"{CB_ANN_VIEW}:{ann_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_ANN_DELETE_OK}:"))
async def cb_ann_delete(callback: CallbackQuery, db: Database, db_user: User) -> None:
    ann_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ok = await repo.delete_announcement(session, db_user.id, ann_id)
        anns = await repo.list_announcements(session, db_user.id)
    if ok:
        await callback.message.edit_text(
            "🗑 O'chirildi.",
            reply_markup=announcements_list_kb(anns),
        )
        await callback.answer()
    else:
        await callback.answer("Xatolik", show_alert=True)
