# ==========================
# Profile Handler
# Version 1.0.0
# ==========================

from bale import Message

from client import bot
from users import get_user
from keyboards import back_menu

from force_join import (
    is_force_join_enabled,
    is_user_joined
)

from force_join_keyboard import force_join_keyboard


@bot.event
async def on_message(message: Message):

    if message.content != "👤 پروفایل":
        return

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
        await message.reply("❌ اطلاعات شما پیدا نشد.")
        return

    subscription = data.get("subscription", {})

    if subscription.get("type"):
        sub_text = (
            f"فعال\n"
            f"نوع: {subscription.get('type')}\n"
            f"پایان: {subscription.get('expire')}"
        )
    else:
        sub_text = "غیرفعال"

    text = (
        "👤 پروفایل شما\n\n"
        f"نام: {data.get('first_name')}\n"
        f"🆔 آیدی: {user.id}\n\n"
        f"💰 کیف پول: {data.get('wallet', 0)} تومان\n\n"
        f"⭐ اشتراک:\n{sub_text}\n\n"
        f"📅 تاریخ عضویت:\n{data.get('join_date')}\n\n"
        f"📢 تعداد کانال‌ها:\n{len(data.get('channels', []))} کانال"
    )

    await message.reply(
        text,
        components=back_menu()
    )