from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.keyboards.inline import CB_ANN_TOGGLE
from bot.texts.uz import (
    BTN_ADMIN,
    BTN_AUTO,
    BTN_CANCEL,
    BTN_COLLECTIONS,
    BTN_DISTRIBUTE,
    BTN_GROUPS,
    BTN_HELP,
    BTN_HOME,
    BTN_LOGS,
    BTN_MY_ANNS,
    BTN_NEW_ANN,
    BTN_SEND,
    BTN_SHARE_PHONE,
    BTN_SKIP,
)

def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def phone_share_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=BTN_SHARE_PHONE, request_contact=True)
    b.adjust(1)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=BTN_NEW_ANN)
    b.button(text=BTN_DISTRIBUTE)
    b.button(text=BTN_MY_ANNS)
    b.button(text=BTN_GROUPS)
    b.button(text=BTN_COLLECTIONS)
    b.button(text=BTN_LOGS)
    b.button(text=BTN_HELP)
    if is_admin:
        b.button(text=BTN_ADMIN)
    b.adjust(2, 2, 2, 1 if is_admin else 0)
    return b.as_markup(resize_keyboard=True, input_field_placeholder="Tugmani tanlang...")


def cancel_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=BTN_CANCEL)
    b.button(text=BTN_HOME)
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)


def skip_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=BTN_SKIP)
    b.button(text=BTN_CANCEL)
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)


def after_save_kb(ann_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="▶️ Faollashtirish", callback_data=f"{CB_ANN_TOGGLE}:{ann_id}"),
                InlineKeyboardButton(text="📡 Tarqatish", callback_data=f"dist_ann:{ann_id}"),
            ],
            [InlineKeyboardButton(text="📋 E'lonlarim", callback_data="ann_list")],
        ]
    )


def confirm_kb(yes_cb: str, no_cb: str, yes_text: str = "✅ Ha") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=yes_text, callback_data=yes_cb),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=no_cb),
            ]
        ]
    )


def ann_save_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Saqlash", callback_data="ann_save"),
                InlineKeyboardButton(text="❌ Bekor", callback_data="ann_cancel"),
            ]
        ]
    )


def ann_type_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚖 Taxi shablon", callback_data="ann_type:taxi")],
            [InlineKeyboardButton(text="✏️ Erkin matn", callback_data="ann_type:free")],
            [InlineKeyboardButton(text="📷 Rasm + matn", callback_data="ann_type:photo")],
        ]
    )
