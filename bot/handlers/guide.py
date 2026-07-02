from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.inline import (
    CB_ANN_LIST,
    CB_ANN_VIEW,
    CB_MAIN,
    announcement_detail_kb,
    announcements_list_kb,
)
from bot.keyboards.menus import (
    after_save_kb,
    ann_save_kb,
    ann_type_menu_kb,
    cancel_kb,
    main_menu_kb,
    skip_kb,
)
from bot.states import AnnouncementStates
from bot.texts.uz import (
    BTN_CANCEL,
    BTN_COLLECTIONS,
    BTN_DISTRIBUTE,
    BTN_GROUPS,
    BTN_HELP,
    BTN_HOME,
    BTN_LOGS,
    BTN_MY_ANNS,
    BTN_NEW_ANN,
    BTN_SKIP,
    FSM_HINT,
    HELP,
    HINT_MY_ANNS,
    HINT_NEW_ANN,
    STEP,
    WELCOME,
)
from bot.utils.html import esc
from bot.utils.phone import validate_phone
from bot.utils.post_body import max_body_chars
from bot.utils.templates import build_taxi_text
from bot.utils.time import format_local

router = Router()

OLD_BTNS = {
    "📢 E'lonlarim": BTN_MY_ANNS,
    "💬 Guruh/Kanallar": BTN_GROUPS,
    "📁 Jamlanmalar": BTN_COLLECTIONS,
    "⏰ Rejalar": BTN_DISTRIBUTE,
    "📤 Hozir yuborish": BTN_DISTRIBUTE,
    "⏰ Avtomatik yuborish": BTN_DISTRIBUTE,
    "ℹ️ Yordam": BTN_HELP,
    "📜 Yuborish tarixi": BTN_LOGS,
}

MENU_BTNS = frozenset({
    BTN_NEW_ANN, BTN_DISTRIBUTE, BTN_MY_ANNS, BTN_GROUPS, BTN_COLLECTIONS,
    BTN_LOGS, BTN_HELP, BTN_HOME, BTN_CANCEL, BTN_SKIP,
    *OLD_BTNS.keys(),
})


def _menu_kb(is_admin: bool = False):
    return main_menu_kb(is_admin=is_admin)


async def _status_text(db: Database, user_id: int) -> str:
    async with db.session_factory() as session:
        d = await repo.get_user_dashboard(session, user_id)
    auto = (
        f"✅ {d['schedules_active']} ta ishlayapti"
        if d["schedules_active"]
        else "❌ yoqilmagan"
    )
    next_send = format_local(d["next_send_at"]) if d.get("next_send_at") else "—"
    last = "—"
    if d.get("last_post_at"):
        icon = "✅" if d.get("last_post_ok") else "❌"
        last = f"{icon} {format_local(d['last_post_at'])}"
    return (
        f"📊 <b>Holatingiz:</b>\n"
        f"• E'lonlar: {d['announcements']} ta\n"
        f"• Tayyor guruhlar: {d['chats_ready']} ta\n"
        f"• Avtomatik: {auto}\n"
        f"• Keyingi yuborish: {next_send}\n"
        f"• Oxirgi yuborish: {last}"
    )


@router.message(F.text == BTN_HOME)
async def cmd_home(
    message: Message,
    db: Database,
    state: FSMContext,
    db_user: User,
    is_super_admin: bool,
) -> None:
    await state.clear()
    name = esc(db_user.full_name or message.from_user.full_name)
    status = await _status_text(db, db_user.id)
    await message.answer(
        WELCOME.format(name=name, status=status),
        reply_markup=_menu_kb(is_super_admin),
    )


@router.message(F.text == BTN_HELP)
async def help_msg(message: Message, is_super_admin: bool) -> None:
    await message.answer(HELP, reply_markup=_menu_kb(is_super_admin))


@router.message(F.text.in_(OLD_BTNS.keys()))
async def old_buttons(
    message: Message, db: Database, db_user: User, is_super_admin: bool, bot: Bot
) -> None:
    mapped = OLD_BTNS[message.text]
    if mapped == BTN_MY_ANNS:
        await my_anns(message, db, db_user, is_super_admin)
    elif mapped == BTN_HELP:
        await help_msg(message, is_super_admin)
    elif mapped == BTN_GROUPS:
        from bot.handlers.chats import groups_menu
        await groups_menu(message, db, db_user, bot, is_super_admin)
    elif mapped == BTN_COLLECTIONS:
        from bot.handlers.collections import collections_entry
        await collections_entry(message, db, db_user, is_super_admin)
    elif mapped == BTN_DISTRIBUTE:
        from bot.handlers.distribute import distribute_menu
        await distribute_menu(message, db, db_user, is_super_admin)
    elif mapped == BTN_LOGS:
        from bot.handlers.logs import logs_menu
        await logs_menu(message, db, db_user, is_super_admin)


@router.message(F.text == BTN_NEW_ANN)
async def new_ann(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AnnouncementStates.choosing_type)
    await message.answer(HINT_NEW_ANN, reply_markup=ann_type_menu_kb())


@router.callback_query(F.data.startswith("ann_type:"))
async def ann_type_pick(callback: CallbackQuery, state: FSMContext) -> None:
    kind = callback.data.split(":")[1]
    await state.update_data(ann_kind=kind)
    if kind == "taxi":
        await state.set_state(AnnouncementStates.waiting_route_from)
        await callback.message.answer(
            STEP.format(
                n=1, total=6,
                text="🚖 <b>Taxi e'lon</b>\n\n<b>Qayerdan?</b>\n<i>Masalan: Toshkent</i>",
            ),
            reply_markup=cancel_kb(),
        )
    elif kind == "free":
        await state.set_state(AnnouncementStates.waiting_name)
        await callback.message.answer(
            "✏️ <b>Erkin matn</b>\n\nE'lon nomi:\n<i>Masalan: Maxsus taklif</i>",
            reply_markup=cancel_kb(),
        )
    else:
        await state.set_state(AnnouncementStates.waiting_name)
        await state.update_data(ann_kind="photo")
        await callback.message.answer(
            "📷 <b>Rasm + matn</b>\n\nE'lon nomi:",
            reply_markup=cancel_kb(),
        )
    await callback.answer()


@router.message(F.text == BTN_MY_ANNS)
async def my_anns(message: Message, db: Database, db_user: User, is_super_admin: bool) -> None:
    async with db.session_factory() as session:
        anns = await repo.list_announcements(session, db_user.id)
    if not anns:
        await message.answer(
            "📋 <b>E'lon yo'q hali</b>\n\n"
            "«🚀 E'lon yaratish» tugmasini bosing — bot sizga qadam-baqadam yordam beradi 👇",
            reply_markup=_menu_kb(is_super_admin),
        )
        return
    await message.answer(HINT_MY_ANNS)
    await message.answer(
        f"📋 <b>E'lonlaringiz</b> ({len(anns)} ta) — tanlang:",
        reply_markup=announcements_list_kb(anns),
    )


# --- Wizard cancel ---

@router.message(
    AnnouncementStates.choosing_type,
    F.text.in_([BTN_CANCEL, BTN_HOME]),
)
@router.message(AnnouncementStates.waiting_name, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_text, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_route_from, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_route_to, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_departure, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_price, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_phone, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_extra, F.text.in_([BTN_CANCEL, BTN_HOME]))
@router.message(AnnouncementStates.waiting_photo, F.text.in_([BTN_CANCEL, BTN_HOME]))
async def wizard_cancel(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=_menu_kb(is_super_admin))


def _guard_menu(message: Message) -> bool:
    if message.text in MENU_BTNS:
        return True
    return False


# --- Free / photo flow ---

@router.message(AnnouncementStates.waiting_name, F.text)
async def w_name(message: Message, state: FSMContext) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    await state.update_data(name=message.text.strip()[:64])
    data = await state.get_data()
    if data.get("ann_kind") == "photo":
        await state.set_state(AnnouncementStates.waiting_photo)
        await message.answer(
            "📷 <b>Rasm + matn — bitta post</b>\n\n"
            "Rasm yuboring va izoh (matn) qo'shing.\n"
            "<i>Yoki avval rasm, keyin matn — ikkala usul ham mumkin.</i>",
            reply_markup=cancel_kb(),
        )
    else:
        await state.set_state(AnnouncementStates.waiting_text)
        await message.answer("✏️ E'lon matnini yozing:", reply_markup=cancel_kb())


@router.message(AnnouncementStates.waiting_text, F.text)
async def w_free_text(message: Message, state: FSMContext, db_user: User) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    text = message.text.strip()
    max_len = max_body_chars(has_photo=False, owner=db_user)
    if len(text) > max_len:
        await message.answer(
            f"Matn juda uzun (maks. ~{max_len} belgi). Qisqartiring.",
            reply_markup=cancel_kb(),
        )
        return
    await state.update_data(text=text)
    await state.set_state(AnnouncementStates.confirming)
    data = await state.get_data()
    preview = data["text"]
    if data.get("photo_file_id"):
        await message.answer(
            f"👁 <b>Post tayyor</b> (rasm + matn)\n\n{preview}\n\n✅ Saqlash tugmasini bosing:",
            reply_markup=ann_save_kb(),
        )
    else:
        await message.answer(
            f"👁 <b>Ko'rinish:</b>\n\n{preview}\n\n✅ To'g'ri bo'lsa «Saqlash» bosing:",
            reply_markup=ann_save_kb(),
        )


@router.message(AnnouncementStates.waiting_photo, F.photo)
async def w_photo(message: Message, state: FSMContext, db_user: User) -> None:
    photo = message.photo[-1]
    caption = (message.caption or "").strip()
    data = await state.get_data()
    if caption:
        max_len = max_body_chars(has_photo=True, owner=db_user)
        if len(caption) > max_len:
            await message.answer(
                f"Matn juda uzun (maks. ~{max_len} belgi). Qisqartiring.",
                reply_markup=cancel_kb(),
            )
            return
        await state.update_data(photo_file_id=photo.file_id, text=caption)
        await state.set_state(AnnouncementStates.confirming)
        await message.answer(
            f"👁 <b>Post ko'rinishi:</b>\n\n{caption}\n\n✅ To'g'ri bo'lsa «Saqlash» bosing:",
            reply_markup=ann_save_kb(),
        )
        return
    await state.update_data(photo_file_id=photo.file_id)
    await state.set_state(AnnouncementStates.waiting_text)
    await message.answer(
        "✏️ Endi rasm ostidagi <b>matnni</b> yozing (bitta post bo'ladi):",
        reply_markup=cancel_kb(),
    )


@router.message(AnnouncementStates.waiting_photo)
async def w_photo_required(message: Message) -> None:
    if message.text == BTN_SKIP:
        await message.answer("Rasm majburiy. Rasm yuboring yoki bekor qiling.", reply_markup=cancel_kb())
        return
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    await message.answer("📷 Iltimos, rasm yuboring.", reply_markup=cancel_kb())


# --- Taxi wizard ---

@router.message(AnnouncementStates.waiting_route_from, F.text)
async def w_from(message: Message, state: FSMContext, db: Database, db_user: User) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    route_from = message.text.strip()[:120]
    async with db.session_factory() as session:
        dup = await repo.find_route_duplicate(session, db_user.id, route_from, "")
    await state.update_data(route_from=route_from)
    await state.set_state(AnnouncementStates.waiting_route_to)
    hint = ""
    if dup:
        hint = f"\n\n⚠️ <i>«{esc(dup.name)}» allaqachon bor — davom etishingiz mumkin.</i>"
    await message.answer(
        STEP.format(n=2, total=6, text=f"<b>Qayerga?</b>\n<i>Masalan: Samarqand</i>{hint}"),
        reply_markup=cancel_kb(),
    )


@router.message(AnnouncementStates.waiting_route_to, F.text)
async def w_to(message: Message, state: FSMContext, db: Database, db_user: User) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    route_to = message.text.strip()[:120]
    data = await state.get_data()
    async with db.session_factory() as session:
        dup = await repo.find_route_duplicate(session, db_user.id, data["route_from"], route_to)
    await state.update_data(route_to=route_to, name=f"{data['route_from']}-{route_to}")
    await state.set_state(AnnouncementStates.waiting_departure)
    hint = f"\n\n⚠️ <i>«{esc(dup.name)}» allaqachon mavjud.</i>" if dup else ""
    await message.answer(
        STEP.format(n=3, total=6, text=f"<b>Qachon?</b>\n<i>Masalan: Bugun 14:00</i>{hint}"),
        reply_markup=cancel_kb(),
    )


@router.message(AnnouncementStates.waiting_departure, F.text)
async def w_time(message: Message, state: FSMContext) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    await state.update_data(departure_time=message.text.strip()[:64])
    await state.set_state(AnnouncementStates.waiting_price)
    await message.answer(
        STEP.format(n=4, total=6, text="<b>Narx?</b>\n<i>Masalan: 150 000 so'm</i>"),
        reply_markup=cancel_kb(),
    )


@router.message(AnnouncementStates.waiting_price, F.text)
async def w_price(message: Message, state: FSMContext) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    await state.update_data(price=message.text.strip()[:64])
    await state.set_state(AnnouncementStates.waiting_phone)
    await message.answer(
        STEP.format(n=5, total=6, text="<b>Telefon?</b>\n<i>Masalan: +998901234567</i>"),
        reply_markup=cancel_kb(),
    )


@router.message(AnnouncementStates.waiting_phone, F.text)
async def w_phone(message: Message, state: FSMContext) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    phone, err = validate_phone(message.text)
    if err:
        await message.answer(f"❌ {err}", reply_markup=cancel_kb())
        return
    await state.update_data(phone=phone)
    await state.set_state(AnnouncementStates.waiting_extra)
    await message.answer(
        STEP.format(
            n=6, total=6,
            text="<b>Qo'shimcha izoh?</b>\n<i>Masalan: 3 o'rin bor</i>\n\nO'tkazib yuborish mumkin.",
        ),
        reply_markup=skip_kb(),
    )


@router.message(AnnouncementStates.waiting_extra, F.text == BTN_SKIP)
async def w_extra_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(extra="")
    await _show_taxi_preview(message, state)


@router.message(AnnouncementStates.waiting_extra, F.text)
async def w_extra(message: Message, state: FSMContext) -> None:
    if _guard_menu(message):
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return
    await state.update_data(extra=message.text.strip()[:200])
    await _show_taxi_preview(message, state)


async def _show_taxi_preview(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = build_taxi_text(
        route_from=data["route_from"],
        route_to=data["route_to"],
        departure_time=data["departure_time"],
        price=data["price"],
        phone=data["phone"],
        extra=data.get("extra", ""),
    )
    await state.update_data(text=text)
    await state.set_state(AnnouncementStates.confirming)
    await message.answer(
        f"👁 <b>Shunday ko'rinadi:</b>\n\n{text}\n\n✅ To'g'ri bo'lsa «Saqlash» bosing:",
        reply_markup=ann_save_kb(),
    )


@router.callback_query(F.data == "ann_save")
async def save_ann(
    callback: CallbackQuery, state: FSMContext, db: Database, db_user: User, is_super_admin: bool
) -> None:
    data = await state.get_data()
    max_len = max_body_chars(has_photo=bool(data.get("photo_file_id")), owner=db_user)
    if len(data.get("text", "")) > max_len:
        await callback.answer(
            f"Matn juda uzun (maks. ~{max_len} belgi). Qayta tahrirlang.",
            show_alert=True,
        )
        return
    async with db.session_factory() as session:
        ann = await repo.create_announcement(
            session,
            user_id=db_user.id,
            name=data["name"],
            text=data["text"],
            photo_file_id=data.get("photo_file_id"),
            phone=data.get("phone"),
            route_from=data.get("route_from"),
            route_to=data.get("route_to"),
            departure_time=data.get("departure_time"),
            price=data.get("price"),
        )
    await state.clear()
    await callback.message.answer(
        f"✅ <b>E'lon saqlandi!</b>\n\n📢 {esc(ann.name)}\n"
        f"⏸ Hozir <b>faol emas</b> — tarqatishdan oldin «▶️ Faollashtirish» bosing.",
        reply_markup=_menu_kb(is_super_admin),
    )
    await callback.message.answer("Keyingi qadamni tanlang 👇", reply_markup=after_save_kb(ann.id))
    await callback.answer("✅ Saqlandi!")


@router.callback_query(F.data == "ann_cancel")
async def cancel_save(callback: CallbackQuery, state: FSMContext, is_super_admin: bool) -> None:
    await state.clear()
    await callback.message.answer("Bekor qilindi.", reply_markup=_menu_kb(is_super_admin))
    await callback.answer()


@router.callback_query(F.data == CB_MAIN)
async def cb_main_menu(callback: CallbackQuery, is_super_admin: bool) -> None:
    await callback.message.answer("🏠 Bosh menyu", reply_markup=_menu_kb(is_super_admin))
    await callback.answer()


@router.callback_query(F.data == CB_ANN_LIST)
async def cb_ann_list(callback: CallbackQuery, db: Database, db_user: User) -> None:
    async with db.session_factory() as session:
        anns = await repo.list_announcements(session, db_user.id)
    await callback.message.edit_text(
        f"📋 E'lonlar ({len(anns)} ta):",
        reply_markup=announcements_list_kb(anns),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_ANN_VIEW}:"))
async def cb_ann_view(callback: CallbackQuery, db: Database, db_user: User) -> None:
    ann_id = int(callback.data.split(":")[1])
    async with db.session_factory() as session:
        ann = await repo.get_announcement(session, db_user.id, ann_id)
    if not ann:
        await callback.answer("Topilmadi", show_alert=True)
        return
    status = "✅ Faol" if ann.is_active else "⏸ O'chirilgan"
    body = ann.text if ann.text else ""
    text = f"📢 <b>{esc(ann.name)}</b> ({status})\n\n{body}"
    try:
        if ann.photo_file_id:
            await callback.message.delete()
            await callback.message.answer_photo(
                ann.photo_file_id, caption=text, reply_markup=announcement_detail_kb(ann)
            )
        else:
            await callback.message.edit_text(text, reply_markup=announcement_detail_kb(ann))
    except Exception:
        await callback.message.answer(text, reply_markup=announcement_detail_kb(ann))
    await callback.answer()
