"""Bot modullarini tekshirish."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    try:
        from bot.config import load_config
        from bot.main import main as bot_main  # noqa: F401
        from bot.database import repository as repo  # noqa: F401
        from bot.services.poster import process_due_schedules  # noqa: F401

        load_config()
        print("OK: barcha modullar yuklandi")
        return 0
    except Exception as exc:
        print(f"XATO: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
