from bale import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from client import bot
from ui import edit_message
from states import set_state, get_state, clear_state
from users import load_users, get_user, set_channel_status
from subscription import subscription_info
from admin_store import (
    is_admin,
    all_admin_ids,
    add_admin,
    remove_admin,
    OWNER_ID,
    load_join_channels,
    save_join_channels,
    resolve_channel,
)
from broadcast_util import run_broadcast, is_forwarded, has_media
from handlers.home import home_components, show_home


def admin_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📨 همگانی", callback_data="ad_bc"), row=1)
    keyboard.add(InlineKeyboardButton("🔒 جوین اجباری", callback_data="ad_join"), row=2)
    keyboard.add(InlineKeyboardButton("👮 ادمین‌ها", callback_data="ad_admins"), row=3)
    keyboard.add(InlineKeyboardButton("📰 آمار اخبار", callback_data="ad_news"), row=4)
    keyboard.add(InlineKeyboardButton("📺 مدیریت کانال‌ها", callback_data="ad_chs"), row=5)
    keyboard.add(InlineKeyboardButton("🔙 منوی اصلی", callback_data="m_home"), row=6)
    return keyboard


def back_admin():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_home"), row=1)
    return keyboard


def all_registered_channels():
    items = []
    users = load_users()
    for user_id, user in users.items():
        if not isinstance(user, dict):
            continue
        for channel in user.get("channels") or []:
            if not isinstance(channel, dict) or not channel.get("id"):
                continue
            item = dict(channel)
            item["owner_id"] = str(user_id)
            item["owner_name"] = user.get("first_name") or ""
            item["owner_username"] = user.get("username") or ""
            items.append(item)
    return items


def mention_of(user_id, user=None):
    user = user or get_user(user_id) or {}
    username = user.get("username")
    if username:
        return "@" + str(username).lstrip("@")
    return str(user_id)


def news_today_text():
    try:
        from analytics import _load, now_tehran
        data = _load()
        day = now_tehran().strftime("%Y-%m-%d")
        messages = data.get("messages") or {}
        lines = ["📰 آمار اخبار امروز", "━━━━━━━━━━━━━━"]
        total = 0
        rows = []
        for channel_id, hours in messages.items():
            count = 0
            if isinstance(hours, dict):
                for key, value in hours.items():
                    if str(key).startswith(day):
                        count += int(value or 0)
            if count:
                rows.append((channel_id, count))
                total += count
        if not rows:
            lines.append("امروز هنوز خبری ارسال نشده.")
        else:
            for channel_id, count in sorted(rows, key=lambda item: item[1], reverse=True):
                lines.append(f"• {channel_id}: {count} خبر")
            lines.append("")
            lines.append(f"📊 جمع همه کانال‌ها: {total} خبر")
        return "\n".join(lines)
    except Exception as error:
        return f"⚠️ خواندن آمار اخبار موفق نبود.\n{error}"


def join_text():
    channels = load_join_channels()
    lines = ["🔒 کانال‌های جوین اجباری", ""]
    for index in range(3):
        if index < len(channels):
            lines.append(f"{index + 1}. {channels[index].get('username') or channels[index].get('id')}")
        else:
            lines.append(f"{index + 1}. ندارد")
    return "\n".join(lines)


def join_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("➕ افزودن کانال", callback_data="ad_join_add"), row=1)
    keyboard.add(InlineKeyboardButton("🗑 حذف کانال", callback_data="ad_join_del"), row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_home"), row=2)
    return keyboard


def admins_text():
    users = load_users()
    lines = [f"👮 تعداد ادمین‌ها: {len(all_admin_ids())}", ""]
    for index, admin_id in enumerate(all_admin_ids(), start=1):
        user = users.get(str(admin_id)) or {}
        lines.append(f"{index}. ایدی عددی: {admin_id}")
        lines.append(f"   یوزرنیم: {mention_of(admin_id, user)}")
        lines.append("")
    return "\n".join(lines)


def admins_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("➕ افزودن", callback_data="ad_adm_add"), row=1)
    keyboard.add(InlineKeyboardButton("🗑 حذف", callback_data="ad_adm_del"), row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_home"), row=2)
    return keyboard


def channels_menu(page=0):
    items = all_registered_channels()
    per_page = 8
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    keyboard = InlineKeyboardMarkup()
    start = page * per_page
    row = 1
    for index, item in enumerate(items[start:start + per_page], start=start):
        status = "🟢" if item.get("status") == "active" else "🔴"
        keyboard.add(InlineKeyboardButton(f"{status} {item['id']}", callback_data=f"ad_ch_{index}"), row=row)
        row += 1
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"ad_chs_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ad_ignore"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"ad_chs_{page+1}"))
    if nav:
        keyboard.add(*nav, row=row)
        row += 1
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_home"), row=row)
    text = f"📺 مدیریت کانال‌ها\n\nتعداد: {len(items)}\nیک کانال را انتخاب کن."
    return text, keyboard


def channel_detail(index):
    items = all_registered_channels()
    if index < 0 or index >= len(items):
        return "کانال پیدا نشد.", back_admin()
    item = items[index]
    owner_id = item.get("owner_id")
    info = subscription_info(owner_id)
    running = item.get("status") == "active"
    text = (
        f"📢 {item['id']}\n"
        "━━━━━━━━━━━━━━\n"
        f"👤 مالک: {mention_of(owner_id)}\n"
        f"📋 اشتراک: {info['remaining']} / {info['total'] or info['remaining']}\n"
        f"⚙️ وضعیت: {'در حال اجرا' if running else 'متوقف'}"
    )
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⏸️ متوقف کردن", callback_data=f"ad_pause_{index}"), row=1)
    keyboard.add(InlineKeyboardButton("▶️ ران کردن", callback_data=f"ad_run_{index}"), row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_chs"), row=2)
    return text, keyboard


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    if data == "ad_ignore":
        return
    if data == "check_force_join":
        from force_join import is_user_joined
        from force_join_keyboard import force_join_keyboard
        if is_user_joined(user_id):
            await show_home(callback, user_id)
        else:
            await edit_message(callback, "🔒 هنوز عضو همه کانال‌ها نشدی.\nعضو شو و دوباره بزن.", force_join_keyboard())
        return
    if not data.startswith("ad_"):
        return
    if not is_admin(user_id):
        await edit_message(callback, "🚫 این بخش فقط برای ادمین است.", home_components(user_id))
        return

    if data in ("ad_home", "ad_panel"):
        clear_state(user_id)
        await edit_message(callback, "🛠 پنل مدیریت\n\nیک گزینه را انتخاب کن.", admin_menu())
        return

    if data == "ad_bc":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👤 همگانی پیوی", callback_data="ad_bc_pv"), row=1)
        keyboard.add(InlineKeyboardButton("📢 همگانی کانال‌ها", callback_data="ad_bc_ch"), row=2)
        keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="ad_home"), row=3)
        await edit_message(callback, "📨 همگانی\n\nکجا ارسال شود؟", keyboard)
        return

    if data in ("ad_bc_pv", "ad_bc_ch"):
        kind = "pv" if data.endswith("pv") else "ch"
        set_state(user_id, "admin_bc", {"kind": kind})
        where = "پیوی کاربرا" if kind == "pv" else "کانال‌های ربات"
        await edit_message(
            callback,
            f"📤 همگانی {where}\n\nمتن عادی را بفرست تا همان روز عادی برود.\nاگر پیام فورواردشده باشد، همان طور فوروارد می‌شود.",
            back_admin(),
        )
        return

    if data == "ad_join":
        clear_state(user_id)
        await edit_message(callback, join_text(), join_menu())
        return
    if data == "ad_join_add":
        if len(load_join_channels()) >= 3:
            await edit_message(callback, "⚠️ بیشتر از ۳ کانال نمی‌شود.", join_menu())
            return
        set_state(user_id, "admin_join_add", {})
        await edit_message(callback, "➕ یوزرنیم کانال را بفرست.\nمثال: @mychannel", back_admin())
        return
    if data == "ad_join_del":
        set_state(user_id, "admin_join_del", {})
        await edit_message(callback, "🗑 یوزرنیم کانال را بفرست تا حذف شود.", back_admin())
        return
    if data == "ad_admins":
        clear_state(user_id)
        await edit_message(callback, admins_text(), admins_menu())
        return
    if data == "ad_adm_add":
        set_state(user_id, "admin_add", {})
        await edit_message(callback, "➕ ایدی عددی کاربر را بفرست تا ادمین شود.", back_admin())
        return
    if data == "ad_adm_del":
        set_state(user_id, "admin_del", {})
        await edit_message(callback, "🗑 ایدی عددی ادمین را بفرست تا حذف شود.", back_admin())
        return
    if data == "ad_news":
        await edit_message(callback, news_today_text(), back_admin())
        return
    if data == "ad_chs" or data.startswith("ad_chs_"):
        page = int(data.replace("ad_chs_", "")) if data.startswith("ad_chs_") and data[7:].isdigit() else 0
        text, keyboard = channels_menu(page)
        await edit_message(callback, text, keyboard)
        return
    if data.startswith("ad_ch_"):
        text, keyboard = channel_detail(int(data.replace("ad_ch_", "")))
        await edit_message(callback, text, keyboard)
        return
    if data.startswith("ad_pause_") or data.startswith("ad_run_"):
        pause = data.startswith("ad_pause_")
        index = int(data.split("_")[-1])
        items = all_registered_channels()
        if index < 0 or index >= len(items):
            await edit_message(callback, "کانال پیدا نشد.", back_admin())
            return
        item = items[index]
        set_channel_status(item["owner_id"], item["id"], "paused" if pause else "active")
        text, keyboard = channel_detail(index)
        prefix = "⏸️ متوقف شد" if pause else "▶️ ران شد"
        await edit_message(callback, prefix + "\n\n" + text, keyboard)


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    state = get_state(user_id)
    name = state.get("state")
    text = (message.content or "").strip()

    if name == "admin_bc":
        kind = (state.get("data") or {}).get("kind") or "pv"
        mid = getattr(message, "message_id", None) or getattr(message, "id", None)
        ok, fail = run_broadcast(
            kind,
            user_id,
            mid,
            text,
            forwarded=is_forwarded(message),
            media=has_media(message),
        )
        clear_state(user_id)
        await message.reply(f"✅ همگانی تمام شد\n\n✔️ موفق: {ok}\n❌ ناموفق: {fail}", components=admin_menu())
        return

    if name == "admin_join_add":
        channel = resolve_channel(text)
        clear_state(user_id)
        items = load_join_channels()
        if not channel:
            await message.reply("⚠️ کانال پیدا نشد.", components=join_menu())
            return
        if len(items) >= 3:
            await message.reply("⚠️ سقف ۳ کانال پر است.", components=join_menu())
            return
        key = str(channel.get("username") or "").lower()
        if any(str(item.get("username") or "").lower() == key for item in items):
            await message.reply("⚠️ این کانال قبلاً هست.", components=join_menu())
            return
        items.append(channel)
        save_join_channels(items)
        await message.reply("✅ اضافه شد.\n\n" + join_text(), components=join_menu())
        return

    if name == "admin_join_del":
        raw = text if text.startswith("@") else "@" + text.lstrip("@")
        items = load_join_channels()
        keep = [item for item in items if str(item.get("username") or "").lower() != raw.lower()]
        save_join_channels(keep)
        clear_state(user_id)
        if len(keep) == len(items):
            await message.reply("⚠️ این کانال در لیست نبود.", components=join_menu())
        else:
            await message.reply("✅ حذف شد.\n\n" + join_text(), components=join_menu())
        return

    if name == "admin_add":
        clear_state(user_id)
        if not text.isdigit():
            await message.reply("⚠️ فقط ایدی عددی بفرست.", components=admins_menu())
            return
        if add_admin(int(text)):
            await message.reply("✅ ادمین اضافه شد.\n\n" + admins_text(), components=admins_menu())
        else:
            await message.reply("⚠️ این کاربر قبلاً ادمین است.", components=admins_menu())
        return

    if name == "admin_del":
        clear_state(user_id)
        if not text.isdigit():
            await message.reply("⚠️ فقط ایدی عددی بفرست.", components=admins_menu())
            return
        target = int(text)
        if target == OWNER_ID:
            await message.reply("⚠️ مالک اصلی حذف نمی‌شود.", components=admins_menu())
            return
        if remove_admin(target):
            await message.reply("✅ حذف شد.\n\n" + admins_text(), components=admins_menu())
        else:
            await message.reply("⚠️ این ایدی ادمین نیست.", components=admins_menu())
