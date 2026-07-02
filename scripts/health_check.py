"""Bot modullarini tekshirish."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def _check_db() -> None:
    from bot.config import load_config
    from bot.database.db import Database

    config = load_config()
    db = Database(config)
    await db.init()
    async with db.session_factory() as session:
        from sqlalchemy import text

        await session.execute(text("SELECT 1"))


def main() -> int:
    try:
        from bot.config import load_config
        from bot.main import main as bot_main  # noqa: F401
        from bot.database import repository as repo  # noqa: F401
        from bot.services.poster import process_due_schedules  # noqa: F401

        load_config()
        asyncio.run(_check_db())
        print("OK: barcha modullar yuklandi, DB ulanishi ishlaydi")
        return 0
    except Exception as exc:
        print(f"XATO: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
