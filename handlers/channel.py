# ==========================
# Channel Handler
# Version 1.3.2
# ==========================

from bale import Message

from client import bot
from users import get_user
from keyboards import (
    channel_menu,
    channel_inline_menu
)

from force_join import (
    is_force_join_enabled,
    is_user_joined
)

from force_join_keyboard import force_join_keyboard


BTN_CHANNEL = "📢 کانال‌های من"


async def show_channels(message: Message):

    user = message.from_user

    # ==========================
    # Force Join
    # ==========================

    if is_force_join_enabled():

        if not is_user_joined(user.id):

            await message.reply(
                "⚠️ برای استفاده از ربات ابتدا در کانال زیر عضو شوید.\n\n"
                "پس از عضویت روی دکمه «✅ عضو شدم» بزنید.",
                components=force_join_keyboard()
            )

            return

    data = get_user(user.id)

    if not data:
        await message.reply("❌ اطلاعات کاربر پیدا نشد.")
        return

    channels = data.get("channels", [])

    if not channels:

        text = (
            "📢 کانال‌های من\n\n"
            "شما هنوز هیچ کانالی ثبت نکرده‌اید.\n\n"
            "برای ثبت کانال جدید، از دکمه زیر استفاده کنید."
        )

        await message.reply(
            text,
            components=channel_menu()
        )

        return

    text = "📢 کانال‌های شما\n\n"

    for index, channel in enumerate(channels, start=1):
        text += f"{index}. {channel['id']}\n"

    text += f"\n\n📊 تعداد کانال‌ها: {len(channels)}/3"

    if len(channels) < 3:
        text += "\n\n⬆️ روی دکمه شیشه‌ای کانال بزنید."
    else:
        text += "\n\n⚠️ حداکثر ۳ کانال ثبت شده است."

    await message.reply(
        text,
        components=channel_inline_menu(channels)
    )

    await message.reply(
        "⬆️ گزینه‌های مدیریت",
        components=channel_menu()
    )


@bot.event
async def on_message(message: Message):

    if message.content != BTN_CHANNEL:
        return

    await show_channels(message)