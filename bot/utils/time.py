from datetime import datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Asia/Tashkent")


def set_timezone(name: str) -> None:
    global _TZ
    _TZ = ZoneInfo(name)


def get_timezone() -> ZoneInfo:
    return _TZ


def utcnow() -> datetime:
    return datetime.now(ZoneInfo("UTC")).replace(tzinfo=None)


def format_local(dt: datetime | None) -> str:
    if not dt:
        return "—"
    local = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(_TZ)
    return local.strftime("%d.%m.%Y %H:%M")
