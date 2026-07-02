import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: tuple[int, ...]
    database_url: str
    scheduler_interval: int
    broadcast_delay: float
    log_level: str
    timezone: str

    @property
    def admin_id(self) -> int:
        return self.admin_ids[0] if self.admin_ids else 0

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_ids


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_raw = os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "")).strip()
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./taxi_bot.db").strip()
    scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "30"))
    broadcast_delay = float(os.getenv("BROADCAST_DELAY_SECONDS", "0.05"))
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    timezone = os.getenv("TIMEZONE", "Asia/Tashkent").strip()

    if not token:
        raise ValueError("BOT_TOKEN .env faylida ko'rsatilmagan")

    admin_ids = tuple(int(x.strip()) for x in admin_raw.split(",") if x.strip())
    if not admin_ids:
        raise ValueError("ADMIN_IDS yoki ADMIN_ID ko'rsatilmagan")

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        database_url=db_url,
        scheduler_interval=scheduler_interval,
        broadcast_delay=broadcast_delay,
        log_level=log_level,
        timezone=timezone,
    )
