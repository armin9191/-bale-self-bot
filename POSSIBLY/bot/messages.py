HEADER = "╭━━━━━━━━━━━━━━━╮\n│ ⚔️ POSSIBLY\n╰━━━━━━━━━━━━━━━╯"


def message(text: str) -> str:
    return f"{HEADER}\n\n{text}"


def success(text: str) -> str:
    return message(f"✅ {text}")


def error(text: str) -> str:
    return message(f"❌ {text}")


def info(text: str) -> str:
    return message(text)


def warning(text: str) -> str:
    return message(f"⚠️ {text}")


def help_text() -> str:
    return info(
        "📖 راهنمای دستورات POSSIBLY\n\n"
        "—— در گروه ——\n"
        "• بن [آیدی] یا ریپلای + بن\n"
        "• کیک [آیدی] یا ریپلای + کیک\n"
        "• آنبن [آیدی] یا ریپلای + آنبن\n"
        "• اکو متن\n"
        "• نجوا متن  (ریپلای به شخص)\n"
        "• یاد بگیر trigger پاسخ\n"
        "• فراموش کن trigger\n"
        "• لیست یادگیری\n"
        "• آمار / امار\n"
        "• دوز\n"
        "• مافیا\n"
        "• جرعت حقیقت\n"
        "• ریپلای به گیف + گیف متن\n\n"
        "—— در پیوی ربات ——\n"
        "• راهنما / منو / start\n"
        "• آمار من\n"
        "• پروفایل\n"
        "• بکاپ  (فقط Owner)\n"
        "• /backup  (فقط Owner)\n\n"
        "ربات فقط در گروه @possibly فعال است."
    )
