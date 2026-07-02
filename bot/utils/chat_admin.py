from aiogram.enums import ChatMemberStatus

ADMIN_STATUSES = {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}


def is_admin_status(status: str | ChatMemberStatus) -> bool:
    return status in ADMIN_STATUSES
