from __future__ import annotations

from bale import InlineKeyboardMarkup, InlineKeyboardButton

from bot.permissions import Role


def private_menu(role: Role) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👤 پروفایل من", callback_data="profile"), row=1)
    kb.add(InlineKeyboardButton("📊 آمار من", callback_data="my_stats"), row=1)
    kb.add(InlineKeyboardButton("🎮 بازی‌ها", callback_data="games"), row=2)
    kb.add(InlineKeyboardButton("📖 راهنما", callback_data="help"), row=2)
    kb.add(InlineKeyboardButton("ℹ️ درباره", callback_data="about"), row=3)
    if role in (Role.ADMIN, Role.OWNER):
        kb.add(InlineKeyboardButton("👥 اعضا", callback_data="members"), row=4)
        kb.add(InlineKeyboardButton("📊 آمار گروه", callback_data="group_stats"), row=4)
        kb.add(InlineKeyboardButton("🧠 یادگیری", callback_data="learning"), row=5)
        kb.add(InlineKeyboardButton("📜 لاگ", callback_data="logs"), row=5)
    if role == Role.OWNER:
        kb.add(InlineKeyboardButton("💾 بکاپ", callback_data="do_backup"), row=6)
    return kb


def ttt_keyboard(board) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for r in range(3):
        for c in range(3):
            i = r * 3 + c
            label = board[i] if board[i] else str(i + 1)
            kb.add(InlineKeyboardButton(str(label), callback_data=f"ttt:{i}"), row=r + 1)
    return kb


def whisper_keyboard(wid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👁 مشاهده نجوا", callback_data=f"whisper:{wid}"), row=1)
    return kb


def whisper_open_keyboard(wid: int) -> InlineKeyboardMarkup:
    """Shown after receiver opens the whisper — OK closes it."""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ OK", callback_data=f"whisper_ok:{wid}"), row=1)
    return kb


def mafia_lobby_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ پیوستن", callback_data="mafia:join"), row=1)
    kb.add(InlineKeyboardButton("➖ خروج", callback_data="mafia:leave"), row=1)
    kb.add(InlineKeyboardButton("▶️ شروع", callback_data="mafia:start"), row=2)
    kb.add(InlineKeyboardButton("⏹ لغو", callback_data="mafia:cancel"), row=2)
    return kb


def tod_lobby_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ پیوستن", callback_data="tod:join"), row=1)
    kb.add(InlineKeyboardButton("➖ خروج", callback_data="tod:leave"), row=1)
    kb.add(InlineKeyboardButton("▶️ شروع", callback_data="tod:start"), row=2)
    return kb


def tod_choice_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("حقیقت", callback_data="tod:truth"), row=1)
    kb.add(InlineKeyboardButton("جرأت", callback_data="tod:dare"), row=1)
    kb.add(InlineKeyboardButton("✅ جواب دادم", callback_data="tod:done"), row=2)
    return kb
