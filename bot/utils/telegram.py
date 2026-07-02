import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from aiogram.exceptions import TelegramRetryAfter

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def with_retry(coro_factory: Callable[[], Awaitable[T]], max_retries: int = 3) -> T:
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except TelegramRetryAfter as exc:
            if attempt == max_retries - 1:
                raise
            wait = exc.retry_after + 1
            logger.warning("Flood control: %ss kutamiz", wait)
            await asyncio.sleep(wait)
    raise RuntimeError("Retry limit")
