from bale import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from client import bot
from ui import edit_message
from users import get_user, add_user, user_exists, set_channel_status, update_user
from keyboards import (
    home_inline_menu,
    channel_inline_menu,
    channel_pick_menu,
    plans_menu,
)
from states import set_state, clear_state
from subscription import (
    subscription_info,
    has_subscription,
    max_channels_for,
    activate_subscription,
    FREE_DAYS,
)
from force_join import is_force_join_enabled, is_user_joined
from force_join_keyboard import force_join_keyboard
from admin_store import is_admin


def back_only():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_home"), row=1)
    return keyboard


def _need_sub_text():
    return (
        "🔒 هنوز اشتراک فعال نداری\n\n"
        "برای استفاده از ربات اول یکی از این دو راه را برو:\n"
        "🎁 اشتراک رایگان ۳ روزه\n"
        "💳 خرید اشتراک"
    )


def home_text(user_id):
    user = get_user(user_id) or {}
    info = subscription_info(user_id)
    channels = user.get("channels") or []
    limit = max_channels_for(user_id) or 1
    if not info["active"]:
        limit = 1
        remain_line = "⏳ مدت باقی‌مانده: ۰ روز"
        sub_line = "📋 اشتراک شما: ندارد"
    else:
        total = info["total"] or info["remaining"]
        remain_line = f"⏳ مدت باقی‌مانده: {info['remaining']}/{total} روز"
        icon = "🎁" if info["type"] == "free" else "⭐"
        sub_line = f"{icon} اشتراک شما: {info['label']}"
    name = user.get("first_name") or "کاربر"
    return (
        f"👋 سلام {name}\n"
        "━━━━━━━━━━━━━━\n"
        f"{sub_line}\n"
        f"{remain_line}\n"
        f"📢 کانال‌های شما: {len(channels)}/{limit}\n"
        "━━━━━━━━━━━━━━\n"
        "از دکمه‌های زیر یکی را انتخاب کن."
    )


def home_components(user_id):
    info = subscription_info(user_id)
    user = get_user(user_id) or {}
    show_free = (not info["active"]) and (not user.get("free_claimed"))
    keyboard = home_inline_menu(show_free=show_free)
    if is_admin(user_id):
        keyboard.add(InlineKeyboardButton("🛠 پنل مدیریت", callback_data="m_admin"), row=8)
    return keyboard


async def show_home(target, user_id, reply=False):
    text = home_text(user_id)
    components = home_components(user_id)
    if reply and callable(getattr(target, "reply", None)):
        await target.reply(text, components=components)
        return
    await edit_message(target, text, components)


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    text = (message.content or "").strip()
    if text != "/start":
        return
    user = message.from_user
    if not user_exists(user.id):
        add_user(user.id, user.first_name, user.username)
    if is_force_join_enabled() and not is_user_joined(user.id):
        await message.reply(
            "🔒 برای شروع کار اول در کانال اطلاع‌رسانی عضو شو.\n\nبعد روی «عضو شدم» بزن.",
            components=force_join_keyboard(),
        )
        return
    await message.reply(home_text(user.id), components=home_components(user.id))


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    user = get_user(user_id) or {}
    channels = user.get("channels") or []

    if data == "m_home":
        clear_state(user_id)
        await show_home(callback, user_id)
        return

    if data == "m_admin":
        if not is_admin(user_id):
            await edit_message(callback, "🚫 این بخش فقط برای ادمین است.", home_components(user_id))
            return
        from handlers.admin_panel import admin_menu
        await edit_message(callback, "🛠 پنل مدیریت\n\nیک گزینه را انتخاب کن.", admin_menu())
        return

    if data == "m_settings":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "📢 هنوز کانالی ثبت نشده.\nاول از «افزودن کانال» کانالت را ثبت کن.", home_components(user_id))
            return
        await edit_message(callback, "⚙️ کدام کانال را می‌خوای تنظیم کنی؟", channel_inline_menu(channels))
        return

    if data == "m_add":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        limit = max_channels_for(user_id)
        if len(channels) >= limit:
            await edit_message(callback, f"🛑 سقف کانال اشتراک شما {limit} تاست.\nبرای سقف بیشتر، اشتراک پولی بخر.", home_components(user_id))
            return
        set_state(user_id, "add_channel", {})
        await edit_message(callback, "➕ آیدی کانال را بفرست.\n\nمثال: @mychannel\n\nربات باید در کانال ادمین باشد.", back_only())
        return

    if data == "m_pause":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "📢 اول یک کانال ثبت کن.", home_components(user_id))
            return
        if len(channels) == 1:
            set_channel_status(user_id, channels[0]["id"], "paused")
            await edit_message(callback, f"⏸️ ارسال متوقف شد\n\nاز الان دیگر در {channels[0]['id']} خبری نمی‌ذارم.", home_components(user_id))
            return
        await edit_message(callback, "⏸️ کدام کانال متوقف شود؟", channel_pick_menu(channels, "pause_"))
        return

    if data.startswith("pause_"):
        channel_id = data.replace("pause_", "", 1)
        set_channel_status(user_id, channel_id, "paused")
        await edit_message(callback, f"⏸️ ارسال متوقف شد\n\nدیگر در {channel_id} خبری نمی‌ذارم.", home_components(user_id))
        return

    if data == "m_resume":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "📢 اول یک کانال ثبت کن.", home_components(user_id))
            return
        if len(channels) == 1:
            channel = channels[0]
            if channel.get("status") == "active":
                await edit_message(callback, f"✅ ربات از قبل در {channel['id']} فعال است.", home_components(user_id))
                return
            set_channel_status(user_id, channel["id"], "active")
            await edit_message(callback, f"▶️ ارسال شروع شد\n\nاز الان در {channel['id']} خبر می‌ذارم.", home_components(user_id))
            return
        await edit_message(callback, "▶️ کدام کانال شروع شود؟", channel_pick_menu(channels, "resume_"))
        return

    if data.startswith("resume_"):
        channel_id = data.replace("resume_", "", 1)
        current = next((item for item in channels if item.get("id") == channel_id), None)
        if current and current.get("status") == "active":
            await edit_message(callback, f"✅ ربات از قبل در {channel_id} فعال است.", home_components(user_id))
            return
        set_channel_status(user_id, channel_id, "active")
        await edit_message(callback, f"▶️ ارسال شروع شد\n\nاز الان در {channel_id} خبر می‌ذارم.", home_components(user_id))
        return

    if data == "m_buy":
        await edit_message(callback, "💳 خرید اشتراک\n\nتعرفه موردنظرت را انتخاب کن.", plans_menu())
        return

    if data == "m_license":
        set_state(user_id, "enter_license", {})
        await edit_message(callback, "🔑 ورود کد لایسنس\n\nکدی که برایت ارسال شده را همین جا بفرست.", back_only())
        return

    if data == "m_free":
        if has_subscription(user_id):
            await edit_message(callback, "✅ همین حالا اشتراک فعال داری.", home_components(user_id))
            return
        if user.get("free_claimed"):
            await edit_message(callback, "🎁 اشتراک رایگان قبلاً گرفته شده.", home_components(user_id))
            return
        activate_subscription(user_id, "free", FREE_DAYS)
        update_user(user_id, {"free_claimed": True})
        await edit_message(callback, f"🎉 اشتراک رایگان {FREE_DAYS} روزه فعال شد", home_components(user_id))
        return

    if data == "m_support":
        await edit_message(callback, "📞 پشتیبانی\n\n👤 @pv_ahzar04", home_components(user_id))
        return
