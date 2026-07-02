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
