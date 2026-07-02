import re

_PHONE_RE = re.compile(r"^\+998\d{9}$")


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw.strip())
    if not digits:
        return None
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 9:
        return f"+998{digits}"
    if raw.strip().startswith("+") and 10 <= len(digits) <= 15:
        return f"+{digits}"
    return None


def validate_phone(raw: str) -> tuple[str | None, str | None]:
    phone = normalize_phone(raw)
    if not phone:
        return None, "Telefon noto'g'ri. Masalan: +998901234567"
    if not _PHONE_RE.match(phone):
        return None, "O'zbekiston raqami: +998 va 9 ta raqam"
    return phone, None
