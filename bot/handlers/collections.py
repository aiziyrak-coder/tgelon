"""Jamlanmalar (guruh to'plamlari) boshqaruvi."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.inline import (
    CB_COL_ADD_CHAT,
    CB_COL_CREATE,
    CB_COL_DELETE,
    CB_COL_DELETE_OK,
    CB_COL_LIST,
    CB_COL_REM_CHAT,
    CB_COL_VIEW,
    CB_COLLECTIONS,
    CB_MAIN,
    collection_detail_kb,
    collections_list_kb,
    collections_menu_kb,
    pick_chat_kb,
)
from bot.keyboards.menus import cancel_kb, confirm_kb, main_menu_kb
from bot.states import CollectionStates
from bot.texts.uz import BTN_CANCEL, BTN_COLLECTIONS, BTN_HOME, DEFAULT_COLLECTION, HINT_COLLECTIONS
from bot.utils.html import esc

router = Router()


@router.message(F.text == BTN_COLLECTIONS)
async def collections_entry(message: Message, db: Database, db_user: User, is_super_admin: bool) -> None:
    async with db.session_factory() as session:
        await repo.ensure_default_collection(session, db_user.id)
        cols = await repo.list_collections(session, db_user.id)
    await message.answer(HINT_COLLECTIONS)
    await message.answer(
        f"📁 <b>Jamlanmalar</b> ({len(cols)} ta)\n"
        f"Standart: «{DEFAULT_COLLECTION}» — tayyor guruhlar avtomatik qo'shiladi.",
        reply_markup=collections_list_kb(cols),
    )


@router.callback_query(F.data == CB_COLLECTIONS)
@router.callback_query(F.data == CB_COL_LIST)
async def cb_col_list(callback: CallbackQuery, db: Database, db_user: User) -> None:
    async with db.session_factory() as session:
        cols = await repo.list_collections(session, db_user.id)
    await callback.message.edit_text(
        f"📁 Jamlanmalar ({len(cols)} ta):",
        reply_markup=collections_list_kb(cols),
    )
    await callback.answer()


@router.callback_query(F.data == CB_COL_CREATE)
async def cb_col_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CollectionStates.waiting_name)
    await callback.message.answer(
        "📁 Yangi jamlanma nomi:\n<i>Masalan: Toshkent guruhlari</i>",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(CollectionStates.waiting_name, F.text.in_([BTN_CANCEL, BTN_HOME]))
async def col_cancel(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.message(CollectionStates.waiting_name, F.text)
async def col_save_name(message: Message, state: FSMContext, db: Database, db_user: User, is_super_admin: bool) -> None:
    name = message.text.strip()[:64]
    if not name:
        await message.answer("Nom bo'sh bo'lmasin.")
        return
    async with db.session_factory() as session:
        col = await repo.create_collection(session, db_user.id, name)
        cols = await repo.list_collections(session, db_user.id)
    await state.clear()
    await message.answer(
        f"✅ <b>{esc(col.name)}</b> yaratildi!",
        reply_markup=collections_list_kb(cols),
    )
    await message.answer("Menyu:", reply_markup=main_menu_kb(is_admin=is_super_admin))


@router.callback_query(F.data.startswith(f"{CB_COL_VIEW}:"))
async def cb_col_view(callback: CallbackQuery, db: Database, db_user: User) -> None:
    col_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        col = await repo.get_collection(session, db_user.id, col_id)
    if not col:
        await callback.answer("Topilmadi", show_alert=True)
        return
    count = len(col.chats) if col.chats else 0
    text = f"📁 <b>{esc(col.name)}</b>\n\nGuruhlar: {count} ta"
    try:
        await callback.message.edit_text(text, reply_markup=collection_detail_kb(col_id))
    except Exception:
        await callback.message.answer(text, reply_markup=collection_detail_kb(col_id))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_COL_ADD_CHAT}:"))
async def cb_col_add_pick(callback: CallbackQuery, db: Database, db_user: User) -> None:
    col_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        chats = await repo.list_chats(session, db_user.id)
        col = await repo.get_collection(session, db_user.id, col_id)
    in_col = {link.chat_id for link in (col.chats or []) if link.chat_id}
    admin_chats = [c for c in chats if c.bot_is_admin]
    if not admin_chats:
        await callback.answer("Admin bo'lgan guruh yo'q", show_alert=True)
        return
    await callback.message.edit_text(
        "Qaysi guruhni qo'shamiz?",
        reply_markup=pick_chat_kb(admin_chats, CB_COL_ADD_CHAT, col_id, in_col),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^col_add:\d+:\d+$"))
async def cb_col_add_save(callback: CallbackQuery, db: Database, db_user: User) -> None:
    parts = callback.data.split(":")
    col_id, chat_id = int(parts[1]), int(parts[2])
    async with db.session_factory() as session:
        ok = await repo.add_chat_to_collection(session, db_user.id, col_id, chat_id)
        col = await repo.get_collection(session, db_user.id, col_id)
    if ok and col:
        count = len(col.chats) if col.chats else 0
        await callback.message.edit_text(
            f"✅ Qo'shildi!\n\n📁 {esc(col.name)} — {count} ta guruh",
            reply_markup=collection_detail_kb(col_id),
        )
        await callback.answer("✅ Qo'shildi")
    else:
        await callback.answer("Xatolik yoki allaqachon bor", show_alert=True)


@router.callback_query(F.data.startswith(f"{CB_COL_REM_CHAT}:"))
async def cb_col_rem_pick(callback: CallbackQuery, db: Database, db_user: User) -> None:
    col_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        col = await repo.get_collection(session, db_user.id, col_id)
    if not col or not col.chats:
        await callback.answer("Guruh yo'q", show_alert=True)
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for link in col.chats:
        if link.chat:
            builder.button(
                text=f"➖ {link.chat.title[:28]}",
                callback_data=f"col_rem:{col_id}:{link.chat.id}",
            )
    builder.button(text="⬅️ Orqaga", callback_data=f"{CB_COL_VIEW}:{col_id}")
    builder.adjust(1)
    await callback.message.edit_text("Olib tashlash uchun tanlang:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.regexp(r"^col_rem:\d+:\d+$"))
async def cb_col_rem_save(callback: CallbackQuery, db: Database, db_user: User) -> None:
    parts = callback.data.split(":")
    col_id, chat_id = int(parts[1]), int(parts[2])
    async with db.session_factory() as session:
        ok = await repo.remove_chat_from_collection(session, db_user.id, col_id, chat_id)
        col = await repo.get_collection(session, db_user.id, col_id)
    if ok and col:
        count = len(col.chats) if col.chats else 0
        await callback.message.edit_text(
            f"✅ Olib tashlandi.\n\n📁 {esc(col.name)} — {count} ta",
            reply_markup=collection_detail_kb(col_id),
        )
        await callback.answer()
    else:
        await callback.answer("Xatolik", show_alert=True)


@router.callback_query(F.data.startswith(f"{CB_COL_DELETE}:"))
async def cb_col_del_ask(callback: CallbackQuery, db: Database, db_user: User) -> None:
    col_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        sched_count = await repo.count_schedules_for_collection(session, db_user.id, col_id)
        col = await repo.get_collection(session, db_user.id, col_id)
    if col and col.name == DEFAULT_COLLECTION:
        await callback.answer("Asosiy jamlanmani o'chirib bo'lmaydi", show_alert=True)
        return
    warn = f"\n\n⚠️ {sched_count} ta avtomatik reja ham o'chadi!" if sched_count else ""
    await callback.message.answer(
        f"🗑 Jamlanmani o'chirasizmi?{warn}",
        reply_markup=confirm_kb(f"{CB_COL_DELETE_OK}:{col_id}", f"{CB_COL_VIEW}:{col_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_COL_DELETE_OK}:"))
async def cb_col_delete(callback: CallbackQuery, db: Database, db_user: User) -> None:
    col_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ok = await repo.delete_collection(session, db_user.id, col_id)
        cols = await repo.list_collections(session, db_user.id)
    if ok:
        await callback.message.edit_text(
            "🗑 O'chirildi.",
            reply_markup=collections_list_kb(cols),
        )
        await callback.answer()
    else:
        await callback.answer("O'chirib bo'lmadi", show_alert=True)
