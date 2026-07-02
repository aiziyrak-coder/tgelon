import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import Config
from bot.database.models import Base

logger = logging.getLogger(__name__)

MIGRATIONS = [
    "ALTER TABLE announcements ADD COLUMN phone VARCHAR(32)",
    "ALTER TABLE announcements ADD COLUMN route_from VARCHAR(120)",
    "ALTER TABLE announcements ADD COLUMN route_to VARCHAR(120)",
    "ALTER TABLE announcements ADD COLUMN departure_time VARCHAR(64)",
    "ALTER TABLE announcements ADD COLUMN price VARCHAR(64)",
    "ALTER TABLE post_logs ADD COLUMN user_id INTEGER",
    "ALTER TABLE post_logs ADD COLUMN chat_title VARCHAR(255)",
    "UPDATE users SET is_active = 1 WHERE is_active IS NULL",
    "ALTER TABLE users ADD COLUMN phone VARCHAR(32)",
    "ALTER TABLE users ADD COLUMN is_registered BOOLEAN DEFAULT 0",
    "ALTER TABLE chats ADD COLUMN user_is_admin BOOLEAN DEFAULT 0",
]


class Database:
    def __init__(self, config: Config) -> None:
        self.engine = create_async_engine(
            config.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await self._run_migrations(conn)
        await self._mark_legacy_users_registered()

    async def _mark_legacy_users_registered(self) -> None:
        """Eski foydalanuvchilarni bir martalik ro'yxatdan o'tgan deb belgilash."""
        sql = text(
            """
            UPDATE users SET is_registered = 1
            WHERE is_registered = 0 AND (
                EXISTS (SELECT 1 FROM announcements WHERE user_id = users.id)
                OR EXISTS (SELECT 1 FROM chats WHERE user_id = users.id)
                OR EXISTS (SELECT 1 FROM schedules WHERE user_id = users.id)
            )
            """
        )
        async with self.session_factory() as session:
            await session.execute(sql)
            await session.commit()

    async def _run_migrations(self, conn) -> None:
        for sql in MIGRATIONS:
            try:
                await conn.execute(text(sql))
            except Exception as exc:
                logger.debug("Migration skip: %s — %s", sql[:60], exc)

    def session(self):
        return self.session_factory()
