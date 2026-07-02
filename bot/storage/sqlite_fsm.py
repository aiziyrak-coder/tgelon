import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

logger = logging.getLogger(__name__)


class SQLiteFSMStorage(BaseStorage):
    """FSM holatini faylda saqlash — qayta ishga tushganda yo'qolmaydi."""

    def __init__(self, path: str = "fsm_storage.json") -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("FSM storage buzilgan, yangi fayl yaratiladi")
                self._data = {}

    async def _save(self) -> None:
        async with self._lock:
            self.path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def _key(self, key: StorageKey) -> str:
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: State | str | None = None) -> None:
        k = self._key(key)
        bucket = self._data.setdefault(k, {})
        bucket["state"] = state.state if isinstance(state, State) else state
        await self._save()

    async def get_state(self, key: StorageKey) -> str | None:
        bucket = self._data.get(self._key(key), {})
        return bucket.get("state")

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        k = self._key(key)
        bucket = self._data.setdefault(k, {})
        bucket["data"] = data
        await self._save()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        bucket = self._data.get(self._key(key), {})
        return bucket.get("data", {})

    async def close(self) -> None:
        await self._save()
