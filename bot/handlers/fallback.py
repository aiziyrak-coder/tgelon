from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.menus import cancel_kb, main_menu_kb
from bot.states import AnnouncementStates, CollectionStates, RegistrationStates, ScheduleStates
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
)

router = Router()

KNOWN = {
    BTN_NEW_ANN, BTN_DISTRIBUTE, BTN_MY_ANNS, BTN_GROUPS, BTN_COLLECTIONS,
    BTN_LOGS, BTN_HELP, BTN_HOME, BTN_CANCEL, BTN_SKIP,
    "📢 E'lonlarim", "💬 Guruh/Kanallar", "📁 Jamlanmalar", "⏰ Rejalar",
    "📤 Hozir yuborish", "⏰ Avtomatik yuborish",
    "ℹ️ Yordam", "📜 Yuborish tarixi", "❌ Bekor qilish", "⏭ Keyingisi",
}

WIZARD_STATES = {
    RegistrationStates.waiting_phone.state,
    RegistrationStates.waiting_name.state,
    AnnouncementStates.choosing_type.state,
    AnnouncementStates.waiting_name.state,
    AnnouncementStates.waiting_text.state,
    AnnouncementStates.waiting_photo.state,
    AnnouncementStates.waiting_route_from.state,
    AnnouncementStates.waiting_route_to.state,
    AnnouncementStates.waiting_departure.state,
    AnnouncementStates.waiting_price.state,
    AnnouncementStates.waiting_phone.state,
    AnnouncementStates.waiting_extra.state,
    AnnouncementStates.waiting_custom_interval.state,
    AnnouncementStates.confirming.state,
    CollectionStates.waiting_name.state,
    ScheduleStates.waiting_custom_interval.state,
    ScheduleStates.waiting_edit_interval.state,
}


@router.message(
    F.text
    & ~F.text.in_(KNOWN)
    & ~F.text.startswith("/")
    & ~F.state(AnnouncementStates.editing_text)
    & ~F.state(AnnouncementStates.editing_photo)
)
async def unknown_message(message: Message, state: FSMContext, is_super_admin: bool) -> None:
    current = await state.get_state()
    if current in WIZARD_STATES:
        await message.answer(FSM_HINT, reply_markup=cancel_kb())
        return

    await message.answer(
        "🤔 Tushunmadim.\n\n"
        "Pastdagi tugmalardan foydalaning yoki /start bosing.",
        reply_markup=main_menu_kb(is_admin=is_super_admin),
    )
