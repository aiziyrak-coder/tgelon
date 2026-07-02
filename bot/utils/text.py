MAX_MESSAGE = 4096
MAX_CAPTION = 1024


def validate_message(text: str, has_photo: bool = False) -> str | None:
    limit = MAX_CAPTION if has_photo else MAX_MESSAGE
    if len(text) > limit:
        return f"Matn juda uzun ({len(text)}/{limit} belgi). Qisqartiring."
    return None


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
