"""Ro'yxatdan o'tmagan foydalanuvchilarni bloklash."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from bot.keyboards.menus import phone_share_kb
from bot.states import RegistrationStates
from bot.texts.uz import REG_REQUIRED, REG_STEP_PHONE


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db_user = data.get("db_user")
        is_super_admin = data.get("is_super_admin", False)

        if not db_user or db_user.is_registered or is_super_admin:
            return await handler(event, data)

        state: FSMContext | None = data.get("state")
        if state:
            current = await state.get_state()
            if current and current.startswith("RegistrationStates"):
                return await handler(event, data)

        msg = _extract_message(event)
        if msg and msg.text and msg.text.startswith("/start"):
            return await handler(event, data)

        if msg and msg.contact and state:
            current = await state.get_state()
            if current == RegistrationStates.waiting_phone.state:
                return await handler(event, data)

        await _prompt_registration(event)
        return None


async def _prompt_registration(event: TelegramObject) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer("Avval ro'yxatdan o'ting!", show_alert=True)
        if event.message:
            await event.message.answer(REG_REQUIRED, reply_markup=phone_share_kb())
        return

    msg = _extract_message(event)
    if msg:
        await msg.answer(REG_STEP_PHONE, reply_markup=phone_share_kb())


def _extract_message(event: TelegramObject) -> Message | None:
    if isinstance(event, Update):
        return event.message or event.edited_message
    if isinstance(event, Message):
        return event
    if isinstance(event, CallbackQuery) and event.message:
        return event.message
    return None
