import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent, TelegramObject

from bot.config import Config, load_config
from bot.database.db import Database
from bot.database import repository as repo
from bot.handlers import admin, announcements, chats, collections, distribute, fallback, guide, logs, my_chat_member, registration, schedules
from bot.keyboards.menus import main_menu_kb
from bot.middlewares.registration import RegistrationMiddleware
from bot.utils.time import set_timezone
from bot.middlewares.user import UserMiddleware
from bot.services.scheduler import PostScheduler
from bot.storage.sqlite_fsm import SQLiteFSMStorage

logger = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)
    file_handler = RotatingFileHandler(
        log_dir / "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        return await handler(event, data)


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config: Config) -> None:
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["config"] = self.config
        return await handler(event, data)


async def main() -> None:
    config = load_config()
    set_timezone(config.timezone)
    setup_logging(config.log_level)

    db = Database(config)
    await db.init()

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    fsm_path = os.getenv("FSM_STORAGE_PATH", str(data_dir / "fsm_storage.json"))

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = SQLiteFSMStorage(fsm_path)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(ConfigMiddleware(config))
    dp.update.middleware(DatabaseMiddleware(db))
    dp.update.middleware(UserMiddleware(db, config))
    dp.update.middleware(RegistrationMiddleware())

    @dp.errors()
    async def on_error(event: ErrorEvent):
        logger.exception("Handler xatosi: %s", event.exception)
        is_admin = False
        try:
            if event.update.message and event.update.message.from_user:
                async with db.session_factory() as session:
                    u = await repo.get_user_by_telegram_id(
                        session, event.update.message.from_user.id
                    )
                if u and config.is_admin(event.update.message.from_user.id):
                    is_admin = True
            if event.update.message:
                await event.update.message.answer(
                    "❌ Kichik xatolik bo'ldi.\n\n/start bosing — hammasi tiklanadi.",
                    reply_markup=main_menu_kb(is_admin=is_admin),
                )
            elif event.update.callback_query:
                await event.update.callback_query.answer(
                    "Xatolik. /start bosing.", show_alert=True
                )
        except Exception:
            pass

    dp.include_router(registration.router)
    dp.include_router(distribute.router)
    dp.include_router(admin.router)
    dp.include_router(guide.router)
    dp.include_router(announcements.router)
    dp.include_router(chats.router)
    dp.include_router(collections.router)
    dp.include_router(logs.router)
    dp.include_router(schedules.router)
    dp.include_router(my_chat_member.router)
    dp.include_router(fallback.router)

    scheduler = PostScheduler(bot, db, config)
    scheduler.start()

    logger.info("Bot ishga tushdi | Admin IDs: %s", config.admin_ids)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await scheduler.stop()
        await storage.close()
        await bot.session.close()
        logger.info("Bot to'xtatildi")


if __name__ == "__main__":
    asyncio.run(main())
