from bale import InlineKeyboardButton

from handlers import home


_original = home.home_components


def home_components(user_id):
    keyboard = _original(user_id)
    try:
        keyboard.add(InlineKeyboardButton("💬 کامنت کانال", callback_data="m_comment"), row=3)
    except Exception:
        pass
    return keyboard


home.home_components = home_components
