from bale import Message
from client import bot


@bot.event
async def on_message(message: Message):
    return