"""Ro'yxatdan o'tish: telefon + ism-familiya."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.db import Database
from bot.database import repository as repo
from bot.database.models import User
from bot.keyboards.menus import main_menu_kb, phone_share_kb, remove_kb
from bot.states import RegistrationStates
from bot.texts.uz import (
    REG_DONE,
    REG_STEP_NAME,
    REG_STEP_PHONE,
    REG_WELCOME,
    REG_WRONG_NAME,
    REG_WRONG_PHONE,
    WELCOME,
)
from bot.utils.html import esc
from bot.utils.phone import normalize_phone

router = Router()


async def begin_registration(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(RegistrationStates.waiting_phone)
    await message.answer(REG_WELCOME, reply_markup=remove_kb())
    await message.answer(REG_STEP_PHONE, reply_markup=phone_share_kb())


async def show_main_menu(
    message: Message, db: Database, db_user: User, is_super_admin: bool
) -> None:
    from bot.handlers.guide import _status_text

    name = esc(db_user.full_name or message.from_user.full_name)
    status = await _status_text(db, db_user.id)
    await message.answer(
        WELCOME.format(name=name, status=status),
        reply_markup=main_menu_kb(is_admin=is_super_admin),
    )


@router.message(CommandStart())
@router.message(Command("start"))
async def reg_start(
    message: Message,
    state: FSMContext,
    db: Database,
    db_user: User,
    is_super_admin: bool,
) -> None:
    if db_user.is_registered or is_super_admin:
        await state.clear()
        await show_main_menu(message, db, db_user, is_super_admin)
        return
    await begin_registration(message, state)


@router.message(RegistrationStates.waiting_phone, F.contact)
async def reg_phone(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer(REG_WRONG_PHONE, reply_markup=phone_share_kb())
        return
    phone = normalize_phone(contact.phone_number)
    if not phone:
        await message.answer(
            "❌ Telefon raqam noto'g'ri. Qayta urinib ko'ring.",
            reply_markup=phone_share_kb(),
        )
        return
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.waiting_name)
    await message.answer(
        f"✅ Raqam qabul qilindi: <b>{esc(phone)}</b>",
        reply_markup=remove_kb(),
    )
    await message.answer(REG_STEP_NAME)


@router.message(RegistrationStates.waiting_phone)
async def reg_phone_invalid(message: Message) -> None:
    await message.answer(REG_WRONG_PHONE, reply_markup=phone_share_kb())


@router.message(RegistrationStates.waiting_name, F.text)
async def reg_name(
    message: Message,
    state: FSMContext,
    db: Database,
    db_user: User,
    is_super_admin: bool,
) -> None:
    name = message.text.strip()
    parts = name.split()
    if len(parts) < 2 or len(name) < 5:
        await message.answer(REG_WRONG_NAME)
        return

    data = await state.get_data()
    phone = data.get("phone")
    if not phone:
        await begin_registration(message, state)
        return

    async with db.session_factory() as session:
        user = await repo.complete_registration(session, db_user.id, phone, name)

    await state.clear()
    if not user:
        await message.answer("Xatolik. /start bosing.")
        return

    await message.answer(
        REG_DONE.format(name=esc(user.full_name), phone=esc(phone)),
        reply_markup=main_menu_kb(is_admin=is_super_admin),
    )
    await message.answer(
        "👇 Quyidagi tugmalardan birini tanlang — bot sizga yo'l ko'rsatadi:",
        reply_markup=main_menu_kb(is_admin=is_super_admin),
    )
