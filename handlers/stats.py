from bale import CallbackQuery

from client import bot
from ui import edit_message
from users import get_user
from keyboards import channel_pick_menu, home_inline_menu
from subscription import has_subscription
from analytics import build_report
from handlers.home import home_components


def _need_sub():
    return "🔒 اول اشتراک را فعال کن تا آمار کانال را ببینی."


def stats_text(report):
    clock = report["now"].strftime("%H:%M")
    lines = [
        f"📊 آمار {report['channel_id']}",
        f"⏰ از ۰۰:۰۰ تا {clock}",
        "━━━━━━━━━━━━━━",
        f"👥 کاربرای امروز: {report['users_today']}",
        f"📅 ۷ روز گذشته: {report['users_7']}",
        f"📆 ۳۰ روز گذشته: {report['users_30']}",
        f"📢 کل اعضا: {report['members']}",
        f"💬 پیام‌های امروز ربات: {report['messages_today']}",
        "━━━━━━━━━━━━━━",
        "📈 پیام هر ساعت:",
    ]
    max_value = max(report["hourly"] or [0]) or 1
    for hour, value in zip(report["hours"], report["hourly"]):
        blocks = int(round((value / max_value) * 8)) if value else 0
        bar = "█" * blocks or "·"
        lines.append(f"{hour:02d}:00  {bar}  {value}")
    return "\n".join(lines)


async def send_channel_stats(user_id, channel_id, callback):
    try:
        report = build_report(channel_id)
        text = stats_text(report)
    except Exception as error:
        print("stats error:", error)
        text = f"⚠️ آمار {channel_id} در حال حاضر درست نشد.\nربات باید در کانال ادمین باشد."
    await edit_message(callback, text, home_components(user_id))


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    user = get_user(user_id) or {}
    channels = user.get("channels") or []

    if data == "m_stats":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "📢 اول یک کانال ثبت کن.", home_components(user_id))
            return
        if len(channels) == 1:
            await send_channel_stats(user_id, channels[0]["id"], callback)
            return
        await edit_message(callback, "📊 آمار کدام کانال را می‌خوای؟", channel_pick_menu(channels, "stats_"))
        return

    if data.startswith("stats_"):
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub(), home_components(user_id))
            return
        await send_channel_stats(user_id, data.replace("stats_", "", 1), callback)
