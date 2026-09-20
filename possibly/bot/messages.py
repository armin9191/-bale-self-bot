HEADER = (
    "╭━━━━━━━━━━━━━━━╮\n"
    "│ ⚔️ POSSIBLY\n"
    "╰━━━━━━━━━━━━━━━╯"
)


def message(text: str) -> str:
    return f"{HEADER}\n\n{text}"


def error(text: str) -> str:
    return message(f"❌ {text}")


def success(text: str) -> str:
    return message(f"✅ {text}")


def info(text: str) -> str:
    return message(text)
