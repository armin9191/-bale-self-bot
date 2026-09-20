```python
# POSSIBLY
# Unified message formatting


HEADER = (
    "╭━━━━━━━━━━━━━━━╮\n"
    "│  POSSIBLY\n"
    "╰━━━━━━━━━━━━━━━╯"
)


def message(text: str) -> str:
    return f"{HEADER}\n{text}"


def success(text: str) -> str:
    return message(f"✅ {text}")


def error(text: str) -> str:
    return message(f"❌ {text}")


def warning(text: str) -> str:
    return message(f"⚠️ {text}")


def info(text: str) -> str:
    return message(text)


def admin(text: str) -> str:
    return message(f"🛡️ {text}")


def game(text: str) -> str:
    return message(f"🎮 {text}")


def stats(text: str) -> str:
    return message(f"📊 {text}")


def learning(text: str) -> str:
    return message(f"🧠 {text}")
```
