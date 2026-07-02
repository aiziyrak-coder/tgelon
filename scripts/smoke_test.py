"""Import va DB smoke test."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    print(f"{'OK' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


async def run() -> int:
    from bot.config import load_config
    from bot.database.db import Database
    from bot.database import repository as repo
    from bot.utils.templates import build_taxi_text

    config = load_config()
    check("Config", True, f"admins={config.admin_ids}")

    db = Database(config)
    await db.init()
    check("Database", True)

    async with db.session_factory() as session:
        user = await repo.get_or_create_user(session, 999999999, "test", "Test")
        col = await repo.ensure_default_collection(session, user.id)
        check("Default collection", col.name == "Asosiy guruhlar")

        text = build_taxi_text("Toshkent", "Samarqand", "14:00", "150000", "+998901234567")
        check("Taxi template", "Toshkent" in text and "Samarqand" in text)

        d = await repo.get_user_dashboard(session, user.id)
        check("Dashboard", "announcements" in d)

    from bot.handlers import admin, announcements, chats, collections, distribute, fallback, guide, logs, my_chat_member, registration, schedules

    check("Handlers", all([admin, announcements, chats, collections, distribute, fallback, guide, logs, my_chat_member, registration, schedules]))

    return 0 if all(c[1] for c in CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
