from bot.database.models import Announcement, User
from bot.utils.html import esc


def build_post_text(announcement: Announcement, owner: User) -> str:
    """E'lon matni + egasi haqida footer (yuborish vaqtida)."""
    lines = [announcement.text, "", "──────────────"]
    name = esc(owner.full_name or "—")
    lines.append(f"👤 <b>E'lon egasi:</b> {name}")
    if owner.phone:
        lines.append(f"📞 {esc(owner.phone)}")
    if owner.username:
        lines.append(f"💬 @{esc(owner.username)}")
    return "\n".join(lines)


def footer_overhead_chars(owner: User) -> int:
    """Footer qo'shilganda qo'shiladigan belgilar (taxminiy)."""
    base = len("\n\n──────────────\n👤 E'lon egasi: \n")
    base += len(owner.full_name or "—")
    if owner.phone:
        base += len(owner.phone) + 4
    if owner.username:
        base += len(owner.username) + 4
    return base


def max_body_chars(has_photo: bool, owner: User) -> int:
    """Telegram limiti minus footer."""
    limit = 1024 if has_photo else 4096
    return max(200, limit - footer_overhead_chars(owner) - 50)
