import html


def esc(text: str) -> str:
    return html.escape(text or "")


def bold(text: str) -> str:
    return f"<b>{esc(text)}</b>"
