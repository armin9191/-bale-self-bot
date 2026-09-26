from datetime import datetime

from bale import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from client import bot
from ui import edit_message
from users import load_users
from admin_store import is_admin, load_join_channels
from subscription import subscription_info, CARD_NUMBER
from handlers import admin_panel
from handlers.admin_panel import back_admin, all_registered_channels
from handlers.home import home_components
from force_join import is_force_join_enabled


def admin_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📨 همگانی", callback_data="ad_bc"), row=1)
    keyboard.add(InlineKeyboardButton("📊 آمار کاربران", callback_data="ad_ustats"), row=2)
    keyboard.add(InlineKeyboardButton("📺 آمار کانال‌ها", callback_data="ad_cstats"), row=2)
    keyboard.add(InlineKeyboardButton("📰 آمار اخبار", callback_data="ad_news"), row=3)
    keyboard.add(InlineKeyboardButton("👤 مدیریت کاربران", callback_data="ad_umgmt"), row=4)
    keyboard.add(InlineKeyboardButton("📺 مدیریت کانال‌ها", callback_data="ad_chs"), row=5)
    keyboard.add(InlineKeyboardButton("👮 ادمین‌ها", callback_data="ad_admins"), row=6)
    keyboard.add(InlineKeyboardButton("🔒 جوین اجباری", callback_data="ad_join"), row=7)
    keyboard.add(InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="ad_set"), row=8)
    keyboard.add(InlineKeyboardButton("🔙 منوی اصلی", callback_data="m_home"), row=9)
    return keyboard


admin_panel.admin_menu = admin_menu


def users_stats_text():
    users = load_users()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_users = 0
    active_sub = 0
    for user in users.values():
        if not isinstance(user, dict):
            continue
        if str(user.get("join_date") or "").startswith(today):
            today_users += 1
    for user_id in users:
        if subscription_info(user_id)["active"]:
            active_sub += 1
    return (
        "📊 آمار کاربران\n"
        "━━━━━━━━━━━━━━\n"
        f"👤 کل کاربران: {len(users)}\n"
        f"🆕 جدید امروز: {today_users}\n"
        f"⭐ اشتراک فعال: {active_sub}"
    )


def channels_stats_text():
    items = all_registered_channels()
    active = sum(1 for item in items if item.get("status") == "active")
    lines = [
        "📺 آمار کانال‌ها",
        "━━━━━━━━━━━━━━",
        f"📢 کل کانال‌ها: {len(items)}",
        f"🟢 فعال: {active}",
        f"🔴 متوقف: {len(items) - active}",
        "",
    ]
    for index, item in enumerate(items[:20], start=1):
        owner = item.get("owner_username") or item.get("owner_id")
        if owner and not str(owner).startswith("@") and not str(owner).isdigit():
            owner = "@" + owner
        lines.append(f"{index}. {item.get('id')} — {owner}")
    if len(items) > 20:
        lines.append(f"\n... و {len(items) - 20} کانال دیگر")
    return "\n".join(lines)


def users_manage_text(page=0):
    users = load_users()
    rows = []
    for user_id, user in users.items():
        if not isinstance(user, dict):
            continue
        info = subscription_info(user_id)
        username = user.get("username")
        mention = ("@" + str(username).lstrip("@")) if username else str(user_id)
        rows.append((user_id, mention, info["label"], len(user.get("channels") or [])))
    per_page = 12
    total_pages = max(1, (len(rows) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    chunk = rows[page * per_page:(page + 1) * per_page]
    lines = [
        "👤 مدیریت کاربران",
        f"صفحه {page + 1}/{total_pages}",
        "━━━━━━━━━━━━━━",
    ]
    for user_id, mention, label, count in chunk:
        lines.append(f"• {mention}\n  ایدی: {user_id} | اشتراک: {label} | کانال: {count}")
    keyboard = InlineKeyboardMarkup()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"ad_umgmt_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"ad_umgmt_{page+1}"))
    if nav:
        keyboard.add(*nav, row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_home"), row=2)
    return "\n".join(lines), keyboard


def settings_text():
    join = load_join_channels()
    status = "روشن" if is_force_join_enabled() and join else "خاموش"
    return (
        "⚙️ تنظیمات ربات\n"
        "━━━━━━━━━━━━━━\n"
        f"💳 کارت: {CARD_NUMBER}\n"
        f"🔒 جوین اجباری: {status}\n"
        f"📢 کانال‌های جوین: {len(join)}/3"
    )


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    if not data.startswith("ad_"):
        return
    if not is_admin(user_id):
        await edit_message(callback, "🚫 این بخش فقط برای ادمین است.", home_components(user_id))
        return
    if data == "ad_ustats":
        await edit_message(callback, users_stats_text(), back_admin())
        return
    if data == "ad_cstats":
        await edit_message(callback, channels_stats_text(), back_admin())
        return
    if data == "ad_umgmt" or data.startswith("ad_umgmt_"):
        page = int(data.replace("ad_umgmt_", "")) if data.startswith("ad_umgmt_") and data[9:].isdigit() else 0
        text, keyboard = users_manage_text(page)
        await edit_message(callback, text, keyboard)
        return
    if data == "ad_set":
        await edit_message(callback, settings_text(), back_admin())
        return
