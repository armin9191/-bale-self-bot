from bale import Message

from client import bot
from users import user_exists, add_user
from force_join import is_force_join_enabled, is_user_joined
from force_join_keyboard import force_join_keyboard


def remove_bottom():
    for name in ("RemoveMenuKeyboard", "MenuKeyboardRemove", "ReplyKeyboardRemove"):
        try:
            mod = __import__("bale", fromlist=[name])
            cls = getattr(mod, name)
            return cls()
        except Exception:
            continue
    try:
        from bale import MenuKeyboardMarkup
        return MenuKeyboardMarkup()
    except Exception:
        return None


@bot.event
async def on_message(message: Message):
    if message.content != "/start":
        return
    user = message.from_user
    if user is None:
        return
    if not user_exists(user.id):
        add_user(user.id, user.first_name, user.username)
    remover = remove_bottom()
    if remover is not None:
        try:
            await message.reply("‌", components=remover)
        except Exception:
            pass
    if is_force_join_enabled() and not is_user_joined(user.id):
        await message.reply(
            "🔒 برای شروع، اول در کانال اطلاع‌رسانی عضو شو.\n\nبعد روی «عضو شدم» بزن.",
            components=force_join_keyboard(),
        )
