"""Ma'lumotlar bazasini zaxiralash."""
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("taxi_bot.db")
DATA_DB = Path("data/taxi_bot.db")
BACKUP_DIR = Path("backups")


def main() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    src = DATA_DB if DATA_DB.exists() else DB
    if not src.exists():
        print("Baza topilmadi")
        return
    dst = BACKUP_DIR / f"taxi_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(src, dst)
    print(f"Zaxira: {dst}")


if __name__ == "__main__":
    main()
