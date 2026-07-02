import asyncio
import logging

from aiogram import Bot

from bot.config import Config
from bot.database.db import Database
from bot.services.poster import process_due_schedules

logger = logging.getLogger(__name__)


class PostScheduler:
    def __init__(self, bot: Bot, db: Database, config: Config) -> None:
        self.bot = bot
        self.db = db
        self.config = config
        self._running = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Post scheduler started (interval=%ss)", self.config.scheduler_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while self._running:
            if self._lock.locked():
                await asyncio.sleep(self.config.scheduler_interval)
                continue
            async with self._lock:
                try:
                    await asyncio.wait_for(
                        process_due_schedules(self.bot, self.db),
                        timeout=120,
                    )
                except asyncio.TimeoutError:
                    logger.error("Scheduler tick timeout (120s)")
                except Exception:
                    logger.exception("Scheduler tick failed")
            await asyncio.sleep(self.config.scheduler_interval)
