"""Guruh va kanallarni boshqarish."""
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.inline import (
    CB_CHAT_DELETE,
    CB_CHAT_DELETE_OK,
    CB_CHAT_LIST,
    CB_CHAT_REFRESH,
    CB_CHAT_TOGGLE,
    CB_CHAT_VIEW,
    CB_CHATS,
    chat_detail_kb,
    chats_list_kb,
)
from bot.keyboards.menus import confirm_kb, main_menu_kb
from bot.services.chat_refresh import refresh_user_chats
from bot.texts.uz import BTN_GROUPS, HINT_GROUPS
from bot.utils.html import esc

router = Router()


@router.message(F.text == BTN_GROUPS)
async def groups_menu(message: Message, db: Database, db_user: User, bot: Bot, is_super_admin: bool) -> None:
    chats = await refresh_user_chats(bot, db, db_user.id, db_user.telegram_id)
    if not chats:
        await message.answer(
            "👥 <b>Guruhlar hali yo'q</b>\n\n"
            "1️⃣ Botni guruh/kanalga qo'shing\n"
            "2️⃣ <b>O'zingiz ham ADMIN</b> bo'ling\n"
            "3️⃣ Botni <b>ADMIN</b> qiling va «Xabar yuborish» bering\n\n"
            "🔗 t.me/taxitgbot?startgroup=true\n\n"
            "<i>⚠️ Siz admin bo'lmasangiz, e'lon tarqatilmaydi.</i>",
            reply_markup=main_menu_kb(is_admin=is_super_admin),
        )
        return
    await message.answer(HINT_GROUPS)
    ready = sum(1 for c in chats if c.bot_is_admin and c.user_is_admin and c.is_active)
    await message.answer(
        f"👥 <b>Guruhlar</b> ({len(chats)} ta, tayyor: {ready})\n\nTanlang:",
        reply_markup=chats_list_kb(chats),
    )


@router.callback_query(F.data == CB_CHATS)
@router.callback_query(F.data == CB_CHAT_LIST)
async def cb_chat_list(callback: CallbackQuery, db: Database, db_user: User, bot: Bot) -> None:
    chats = await refresh_user_chats(bot, db, db_user.id, db_user.telegram_id)
    if not chats:
        await callback.message.edit_text("Guruh yo'q.")
        await callback.answer()
        return
    ready = sum(1 for c in chats if c.bot_is_admin and c.user_is_admin and c.is_active)
    await callback.message.edit_text(
        f"👥 Guruhlar ({len(chats)} ta, tayyor: {ready}):",
        reply_markup=chats_list_kb(chats),
    )
    await callback.answer()


@router.callback_query(F.data == CB_CHAT_REFRESH)
async def cb_chat_refresh(callback: CallbackQuery, db: Database, db_user: User, bot: Bot) -> None:
    chats = await refresh_user_chats(bot, db, db_user.id, db_user.telegram_id)
    ready = sum(1 for c in chats if c.bot_is_admin and c.user_is_admin and c.is_active)
    await callback.message.edit_text(
        f"🔄 Yangilandi!\n\nTayyor: {ready} ta (siz + bot admin)",
        reply_markup=chats_list_kb(chats),
    )
    await callback.answer("✅ Yangilandi")


@router.callback_query(F.data.startswith(f"{CB_CHAT_VIEW}:"))
async def cb_chat_view(callback: CallbackQuery, db: Database, db_user: User) -> None:
    chat_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        chat = await repo.get_chat(session, db_user.id, chat_id)
    if not chat:
        await callback.answer("Topilmadi", show_alert=True)
        return
    bot_a = "✅ Admin" if chat.bot_is_admin else "❌ Admin emas"
    user_a = "✅ Admin" if chat.user_is_admin else "❌ Siz admin emassiz"
    ready = "✅ Tarqatish mumkin" if chat.is_active and chat.bot_is_admin and chat.user_is_admin else "⚠️ Tayyor emas"
    typ = "📢 Kanal" if chat.chat_type == "channel" else "👥 Guruh"
    text = (
        f"{typ} <b>{esc(chat.title)}</b>\n\n"
        f"Bot: {bot_a}\n"
        f"Siz: {user_a}\n"
        f"Holat: {ready}"
    )
    try:
        await callback.message.edit_text(text, reply_markup=chat_detail_kb(chat))
    except Exception:
        await callback.message.answer(text, reply_markup=chat_detail_kb(chat))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_CHAT_TOGGLE}:"))
async def cb_chat_toggle(callback: CallbackQuery, db: Database, db_user: User) -> None:
    chat_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        chat = await repo.get_chat(session, db_user.id, chat_id)
        if chat and chat.bot_is_admin and chat.user_is_admin:
            await repo.toggle_chat_active(session, db_user.id, chat_id)
            chat = await repo.get_chat(session, db_user.id, chat_id)
        elif chat:
            await callback.answer("Siz va bot admin bo'lmaguncha yoqib bo'lmaydi", show_alert=True)
            return
    if chat:
        status = "yoqildi" if chat.is_active else "o'chirildi"
        await callback.message.edit_reply_markup(reply_markup=chat_detail_kb(chat))
        await callback.answer(f"Guruh {status}")
    else:
        await callback.answer("Xatolik", show_alert=True)


@router.callback_query(F.data.startswith(f"{CB_CHAT_DELETE}:"))
async def cb_chat_del_ask(callback: CallbackQuery) -> None:
    chat_id = callback.data.split(":")[1]
    await callback.message.answer(
        "🗑 Guruhni ro'yxatdan o'chirasizmi?",
        reply_markup=confirm_kb(f"{CB_CHAT_DELETE_OK}:{chat_id}", f"{CB_CHAT_VIEW}:{chat_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_CHAT_DELETE_OK}:"))
async def cb_chat_delete(callback: CallbackQuery, db: Database, db_user: User, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ok = await repo.delete_chat(session, db_user.id, chat_id)
    if ok:
        chats = await refresh_user_chats(bot, db, db_user.id, db_user.telegram_id)
        if chats:
            await callback.message.edit_text("🗑 O'chirildi.", reply_markup=chats_list_kb(chats))
        else:
            await callback.message.edit_text("🗑 O'chirildi. Guruh qolmadi.")
        await callback.answer()
    else:
        await callback.answer("Xatolik", show_alert=True)
