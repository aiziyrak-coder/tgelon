from bot.utils.html import bold, esc


def build_taxi_text(
    route_from: str,
    route_to: str,
    departure_time: str,
    price: str,
    phone: str,
    extra: str = "",
) -> str:
    lines = [
        "🚖 " + bold("Shaharlararo TAXI"),
        "",
        f"📍 {bold('Yonalish:')} {esc(route_from)} → {esc(route_to)}",
        f"🕐 {bold('Vaqt:')} {esc(departure_time)}",
        f"💰 {bold('Narx:')} {esc(price)}",
        f"📞 {bold('Telefon:')} {esc(phone)}",
    ]
    if extra.strip():
        lines.extend(["", esc(extra.strip())])
    return "\n".join(lines)
