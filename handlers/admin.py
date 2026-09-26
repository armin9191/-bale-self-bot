from bale import Message

from client import bot
from admin_store import is_admin
from handlers.admin_panel import admin_menu


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    if (message.content or "").strip() != "🛠 پنل مدیریت":
        return
    if not is_admin(message.from_user.id):
        return
    await message.reply("🛠 پنل مدیریت\n\nیک گزینه را انتخاب کن.", components=admin_menu())
