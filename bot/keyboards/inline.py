from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import Announcement, Chat, ChatCollection, Schedule

CB_MAIN = "main"
CB_ANNOUNCEMENTS = "ann"
CB_CHATS = "chats"
CB_COLLECTIONS = "cols"
CB_SCHEDULES = "sched"
CB_LOGS = "logs"
CB_ADMIN = "admin"
CB_CANCEL = "cancel"
CB_CONFIRM = "cfm"
CB_DENY = "deny"

CB_ANN_LIST = "ann_list"
CB_ANN_CREATE = "ann_create"
CB_ANN_CREATE_TAXI = "ann_taxi"
CB_ANN_CREATE_FREE = "ann_free"
CB_ANN_VIEW = "ann_view"
CB_ANN_EDIT_TEXT = "ann_edit_text"
CB_ANN_EDIT_PHOTO = "ann_edit_photo"
CB_ANN_TOGGLE = "ann_toggle"
CB_ANN_DELETE = "ann_delete"
CB_ANN_DELETE_OK = "ann_del_ok"
CB_ANN_SEND_NOW = "ann_send_now"
CB_ANN_PICK_COL = "ann_pick_col"
CB_ANN_PREVIEW = "ann_preview"
CB_ANN_CONFIRM_SAVE = "ann_save"

CB_CHAT_LIST = "chat_list"
CB_CHAT_VIEW = "chat_view"
CB_CHAT_TOGGLE = "chat_toggle"
CB_CHAT_DELETE = "chat_delete"
CB_CHAT_DELETE_OK = "chat_del_ok"
CB_CHAT_REFRESH = "chat_refresh"

CB_COL_LIST = "col_list"
CB_COL_CREATE = "col_create"
CB_COL_VIEW = "col_view"
CB_COL_DELETE = "col_delete"
CB_COL_DELETE_OK = "col_del_ok"
CB_COL_ADD_CHAT = "col_add"
CB_COL_REM_CHAT = "col_rem"

CB_SCHED_LIST = "sched_list"
CB_SCHED_CREATE = "sched_create"
CB_SCHED_VIEW = "sched_view"
CB_SCHED_TOGGLE = "sched_toggle"
CB_SCHED_DELETE = "sched_delete"
CB_SCHED_DELETE_OK = "sched_del_ok"
CB_SCHED_EDIT_INT = "sched_edit_int"
CB_SCHED_PICK_ANN = "sched_ann"
CB_SCHED_PICK_COL = "sched_col"
CB_SCHED_PICK_INT = "sched_int"
CB_SCHED_CUSTOM_INT = "sched_custom"

CB_ADMIN_STATS = "adm_stats"
CB_ADMIN_USERS = "adm_users"
CB_ADMIN_USER = "adm_user"
CB_ADMIN_BLOCK = "adm_block"
CB_ADMIN_UNBLOCK = "adm_unblock"
CB_ADMIN_BROADCAST = "adm_bc"
CB_ADMIN_LOGS = "adm_logs"


def announcements_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Ro'yxat", callback_data=CB_ANN_LIST)
    builder.button(text="➕ Yangi e'lon", callback_data=CB_ANN_CREATE)
    builder.button(text="⬅️ Bosh menyu", callback_data=CB_MAIN)
    builder.adjust(2, 1)
    return builder.as_markup()


def ann_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚖 Taxi shablon", callback_data=CB_ANN_CREATE_TAXI)
    builder.button(text="✏️ Erkin matn", callback_data=CB_ANN_CREATE_FREE)
    builder.button(text="⬅️ Orqaga", callback_data=CB_ANNOUNCEMENTS)
    builder.adjust(1)
    return builder.as_markup()


def announcements_list_kb(
    announcements: list[Announcement],
    *,
    for_auto: bool = False,
    for_send: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ann in announcements:
        status = "✅" if ann.is_active else "⏸"
        if for_auto:
            cb = f"quick_auto:{ann.id}"
        elif for_send:
            cb = f"send_ask:{ann.id}"
        else:
            cb = f"{CB_ANN_VIEW}:{ann.id}"
        builder.button(text=f"{status} {ann.name}", callback_data=cb)
    builder.adjust(1)
    return builder.as_markup()


def active_schedules_kb(schedules: list[Schedule]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sch in schedules:
        if not sch.is_active:
            continue
        ann = sch.announcement.name if sch.announcement else "?"
        builder.button(
            text=f"⏸ {ann} ({sch.interval_minutes} daq)",
            callback_data=f"{CB_SCHED_TOGGLE}:{sch.id}",
        )
    builder.button(text="➕ Yangi tarqatish qo'shish", callback_data="dist_new")
    builder.adjust(1)
    return builder.as_markup()


DIST_INTERVALS = [1, 2, 5, 10, 15]


def dist_ann_list_kb(announcements: list[Announcement]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ann in announcements:
        builder.button(text=f"📢 {ann.name}", callback_data=f"dist_ann:{ann.id}")
    builder.adjust(1)
    return builder.as_markup()


def dist_collection_kb(
    ann_id: int,
    collections: list[ChatCollection],
    counts: dict[int, int],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for col in collections:
        n = counts.get(col.id, 0)
        builder.button(
            text=f"📁 {col.name} ({n} ta tayyor)",
            callback_data=f"dist_col:{ann_id}:{col.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def dist_interval_kb(ann_id: int, col_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minutes in DIST_INTERVALS:
        builder.button(
            text=f"▶️ Har {minutes} daqiqa",
            callback_data=f"dist_start:{ann_id}:{col_id}:{minutes}",
        )
    builder.button(text="📤 Faqat 1 marta yuborish", callback_data=f"dist_once:{ann_id}:{col_id}")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def announcement_detail_kb(ann: Announcement) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📡 E'lon tarqatish", callback_data=f"dist_ann:{ann.id}")
    builder.button(text="✏️ Matnni o'zgartirish", callback_data=f"{CB_ANN_EDIT_TEXT}:{ann.id}")
    builder.button(text="📷 Rasmni o'zgartirish", callback_data=f"{CB_ANN_EDIT_PHOTO}:{ann.id}")
    toggle = "⏸ To'xtatish" if ann.is_active else "▶️ Yoqish"
    builder.button(text=toggle, callback_data=f"{CB_ANN_TOGGLE}:{ann.id}")
    builder.button(text="🗑 O'chirish", callback_data=f"{CB_ANN_DELETE}:{ann.id}")
    builder.button(text="⬅️ Ro'yxat", callback_data=CB_ANN_LIST)
    builder.adjust(1)
    return builder.as_markup()


def ann_confirm_save_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Saqlash", callback_data=CB_ANN_CONFIRM_SAVE)
    builder.button(text="❌ Bekor", callback_data=CB_ANNOUNCEMENTS)
    builder.adjust(2)
    return builder.as_markup()


def chats_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Ro'yxat", callback_data=CB_CHAT_LIST)
    builder.button(text="🔄 Holatni yangilash", callback_data=CB_CHAT_REFRESH)
    builder.button(text="⬅️ Bosh menyu", callback_data=CB_MAIN)
    builder.adjust(1)
    return builder.as_markup()


def chats_list_kb(chats: list[Chat]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for chat in chats:
        if chat.bot_is_admin and chat.user_is_admin:
            status = "✅"
        elif chat.bot_is_admin:
            status = "⚠️"
        else:
            status = "❌"
        type_icon = "📢" if chat.chat_type == "channel" else "👥"
        builder.button(
            text=f"{status}{type_icon} {chat.title[:28]}",
            callback_data=f"{CB_CHAT_VIEW}:{chat.id}",
        )
    builder.button(text="⬅️ Orqaga", callback_data=CB_CHATS)
    builder.adjust(1)
    return builder.as_markup()


def chat_detail_kb(chat: Chat) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "⏸ O'chirish" if chat.is_active else "▶️ Yoqish"
    builder.button(text=toggle_text, callback_data=f"{CB_CHAT_TOGGLE}:{chat.id}")
    builder.button(text="🗑 O'chirish", callback_data=f"{CB_CHAT_DELETE}:{chat.id}")
    builder.button(text="⬅️ Ro'yxat", callback_data=CB_CHAT_LIST)
    builder.adjust(1)
    return builder.as_markup()


def collections_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Ro'yxat", callback_data=CB_COL_LIST)
    builder.button(text="➕ Yangi jamlanma", callback_data=CB_COL_CREATE)
    builder.button(text="⬅️ Bosh menyu", callback_data=CB_MAIN)
    builder.adjust(2, 1)
    return builder.as_markup()


def collections_list_kb(collections: list[ChatCollection]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for col in collections:
        count = len(col.chats) if col.chats else 0
        builder.button(
            text=f"📁 {col.name} ({count})",
            callback_data=f"{CB_COL_VIEW}:{col.id}",
        )
    builder.button(text="➕ Yangi jamlanma", callback_data=CB_COL_CREATE)
    builder.button(text="⬅️ Orqaga", callback_data=CB_COLLECTIONS)
    builder.adjust(1)
    return builder.as_markup()


def collection_detail_kb(col_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Guruh qo'shish", callback_data=f"{CB_COL_ADD_CHAT}:{col_id}")
    builder.button(text="➖ Guruh olib tashlash", callback_data=f"{CB_COL_REM_CHAT}:{col_id}")
    builder.button(text="🗑 O'chirish", callback_data=f"{CB_COL_DELETE}:{col_id}")
    builder.button(text="⬅️ Ro'yxat", callback_data=CB_COL_LIST)
    builder.adjust(1)
    return builder.as_markup()


def pick_chat_kb(
    chats: list[Chat], prefix: str, extra_id: int, in_collection_ids: set[int] | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    in_collection_ids = in_collection_ids or set()
    for chat in chats:
        if not chat.bot_is_admin:
            continue
        mark = "✓ " if chat.id in in_collection_ids else ""
        builder.button(
            text=f"{mark}{chat.title[:28]}",
            callback_data=f"{prefix}:{extra_id}:{chat.id}",
        )
    builder.button(text="⬅️ Orqaga", callback_data=f"{CB_COL_VIEW}:{extra_id}")
    builder.adjust(1)
    return builder.as_markup()


def schedules_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Ro'yxat", callback_data=CB_SCHED_LIST)
    builder.button(text="➕ Yangi reja", callback_data=CB_SCHED_CREATE)
    builder.button(text="⬅️ Bosh menyu", callback_data=CB_MAIN)
    builder.adjust(2, 1)
    return builder.as_markup()


def schedules_list_kb(schedules: list[Schedule]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sch in schedules:
        status = "✅" if sch.is_active else "⏸"
        ann_name = sch.announcement.name if sch.announcement else "?"
        col_name = sch.collection.name if sch.collection else "?"
        builder.button(
            text=f"{status} {ann_name} → {col_name} ({sch.interval_minutes}d)",
            callback_data=f"{CB_SCHED_VIEW}:{sch.id}",
        )
    builder.button(text="➕ Yangi reja", callback_data=CB_SCHED_CREATE)
    builder.button(text="⬅️ Orqaga", callback_data=CB_SCHEDULES)
    builder.adjust(1)
    return builder.as_markup()


def schedule_detail_kb(sch: Schedule) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle = "⏸ To'xtatish" if sch.is_active else "▶️ Yoqish"
    builder.button(text=toggle, callback_data=f"{CB_SCHED_TOGGLE}:{sch.id}")
    builder.button(text="⏱ Vaqtni o'zgartirish", callback_data=f"{CB_SCHED_EDIT_INT}:{sch.id}")
    builder.button(text="🗑 O'chirish", callback_data=f"{CB_SCHED_DELETE}:{sch.id}")
    builder.adjust(1)
    return builder.as_markup()


def pick_announcement_kb(announcements: list[Announcement], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ann in announcements:
        if ann.is_active:
            builder.button(text=ann.name, callback_data=f"{prefix}:{ann.id}")
    builder.button(text="⬅️ Orqaga", callback_data=CB_SCHEDULES)
    builder.adjust(1)
    return builder.as_markup()


def pick_collection_kb(collections: list[ChatCollection], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for col in collections:
        builder.button(text=col.name, callback_data=f"{prefix}:{col.id}")
    builder.button(text="⬅️ Orqaga", callback_data=CB_SCHEDULES)
    builder.adjust(1)
    return builder.as_markup()


INTERVAL_OPTIONS = [
    (15, "15 daqiqa"),
    (30, "30 daqiqa"),
    (45, "45 daqiqa"),
    (60, "1 soat"),
    (120, "2 soat"),
    (180, "3 soat"),
    (360, "6 soat"),
    (720, "12 soat"),
    (1440, "24 soat"),
]


def pick_interval_kb(ann_id: int, col_id: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minutes, label in INTERVAL_OPTIONS:
        if col_id == 0:
            cb = f"auto_set:{ann_id}:{minutes}"
        else:
            cb = f"{CB_SCHED_PICK_INT}:{ann_id}:{col_id}:{minutes}"
        builder.button(text=label, callback_data=cb)
    if col_id == 0:
        builder.button(text="✏️ Boshqa vaqt", callback_data=f"auto_custom:{ann_id}")
    elif col_id != 0:
        builder.button(
            text="✏️ Boshqa vaqt",
            callback_data=f"{CB_SCHED_CUSTOM_INT}:{ann_id}:{col_id}",
        )
    builder.adjust(2)
    return builder.as_markup()


def pick_interval_edit_kb(sched_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minutes, label in INTERVAL_OPTIONS:
        builder.button(
            text=label,
            callback_data=f"{CB_SCHED_EDIT_INT}:{sched_id}:{minutes}",
        )
    builder.button(text="✏️ Boshqa vaqt", callback_data=f"sched_custom:{sched_id}")
    builder.button(text="⬅️ Orqaga", callback_data=f"{CB_SCHED_VIEW}:{sched_id}")
    builder.adjust(2)
    return builder.as_markup()


def pick_collection_for_send_kb(collections: list[ChatCollection], ann_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for col in collections:
        builder.button(
            text=col.name,
            callback_data=f"{CB_ANN_PICK_COL}:{ann_id}:{col.id}",
        )
    builder.button(text="⬅️ Orqaga", callback_data=f"{CB_ANN_VIEW}:{ann_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data=CB_ADMIN_STATS)
    builder.button(text="👥 Foydalanuvchilar", callback_data=CB_ADMIN_USERS)
    builder.button(text="📣 Hammaga xabar", callback_data=CB_ADMIN_BROADCAST)
    builder.button(text="📜 So'nggi loglar", callback_data=CB_ADMIN_LOGS)
    builder.button(text="⬅️ Bosh menyu", callback_data=CB_MAIN)
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_users_kb(users: list, page: int, total: int, page_size: int = 10) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        status = "🚫" if user.is_blocked else "✅"
        name = user.full_name or user.username or str(user.telegram_id)
        builder.button(
            text=f"{status} {name[:25]}",
            callback_data=f"{CB_ADMIN_USER}:{user.id}",
        )
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"{CB_ADMIN_USERS}:{page-1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"{CB_ADMIN_USERS}:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.button(text="⬅️ Orqaga", callback_data=CB_ADMIN)
    builder.adjust(1)
    return builder.as_markup()


def admin_user_detail_kb(user_id: int, is_blocked: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_blocked:
        builder.button(text="✅ Blokdan chiqarish", callback_data=f"{CB_ADMIN_UNBLOCK}:{user_id}")
    else:
        builder.button(text="🚫 Bloklash", callback_data=f"{CB_ADMIN_BLOCK}:{user_id}")
    builder.button(text="⬅️ Ro'yxat", callback_data=f"{CB_ADMIN_USERS}:0")
    builder.adjust(1)
    return builder.as_markup()
