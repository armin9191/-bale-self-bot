from bale import Message

from client import bot
from states import clear_state


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    if (message.content or "") in ("🏠 منوی اصلی", "🔙 بازگشت"):
        clear_state(message.from_user.id)
        from handlers.home import home_text, home_components
        await message.reply(
            home_text(message.from_user.id),
            components=home_components(message.from_user.id),
        )
