# ==========================
# Help Handler
# Version 1.0.0
# ==========================

from bale import Message

from client import bot

from force_join import (
    is_force_join_enabled,
    is_user_joined
)

from force_join_keyboard import force_join_keyboard


@bot.event
async def on_message(message: Message):

    if message.content != "📖 راهنما":
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

    await message.reply(
        "📖 راهنمای ربات\n\n"
        "• از بخش «📢 کانال‌های من» کانال خود را ثبت کنید.\n"
        "• نسخه رایگان امکان ثبت حداکثر ۳ کانال را دارد.\n"
        "• اخبار به‌صورت خودکار در کانال‌های ثبت‌شده ارسال می‌شوند.\n"
        "• برای دریافت امکانات بیشتر می‌توانید اشتراک Pro تهیه کنید.\n\n"
        "📞 اگر سؤال یا مشکلی داشتید، از بخش «پشتیبانی» با ما در ارتباط باشید."
    )