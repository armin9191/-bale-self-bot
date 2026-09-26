from bale import Message

from client import bot
from states import get_state, clear_state
from users import add_channel, get_user
from subscription import has_subscription, max_channels_for
from handlers.home import home_components
from channel_utils import normalize_channel_id, channel_exists, bot_is_admin


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    if get_state(user_id).get("state") != "add_channel":
        return
    text = (message.content or "").strip()
    if text in ("/start", "🔙 بازگشت", "🏠 منوی اصلی"):
        return
    if not has_subscription(user_id):
        clear_state(user_id)
        await message.reply(
            "🔒 اشتراک فعال نداری.\nاول اشتراک رایگان یا خرید اشتراک را انتخاب کن.",
            components=home_components(user_id),
        )
        return
    channel = normalize_channel_id(text)
    if not channel:
        await message.reply("⚠️ آیدی کانال درست نیست.\nمثال: @mychannel")
        return
    user = get_user(user_id) or {}
    existing = [str(item.get("id") or "").lower() for item in user.get("channels") or []]
    if channel.lower() in existing:
        await message.reply(
            f"⚠️ {channel} قبلاً ثبت شده.",
            components=home_components(user_id),
        )
        return
    limit = max_channels_for(user_id)
    if len(user.get("channels") or []) >= limit:
        clear_state(user_id)
        await message.reply(
            f"🛑 سقف کانال اشتراک شما {limit} تاست.",
            components=home_components(user_id),
        )
        return
    ok, info = channel_exists(channel)
    if not ok:
        await message.reply(f"⚠️ کانال پیدا نشد.\n{info}")
        return
    ok, info = bot_is_admin(channel)
    if not ok:
        await message.reply(
            f"⚠️ اول ربات را در {channel} ادمین کن، بعد دوباره همین آیدی را بفرست.\n{info}"
        )
        return
    if add_channel(user_id, channel, max_channels=limit):
        clear_state(user_id)
        await message.reply(
            f"✅ کانال {channel} ثبت شد.\nاز تنظیمات می‌تونی دسته و فاصله ارسال را عوض کنی.",
            components=home_components(user_id),
        )
        return
    await message.reply(
        "⚠️ ثبت کانال موفق نبود. دوباره تلاش کن.",
        components=home_components(user_id),
    )
