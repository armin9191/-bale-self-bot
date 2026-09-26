from bale import (
    MenuKeyboardMarkup,
    MenuKeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from subscription import PLANS

BTN_PROFILE = "👤 پروفایل"
BTN_WALLET = "💰 کیف پول"
BTN_CHANNEL = "📢 کانال‌های من"
BTN_ADD_CHANNEL = "➕ افزودن کانال جدید"
BTN_REFERRAL = "🎁 دعوت دوستان"
BTN_SUBSCRIPTION = "💳 خرید اشتراک"
BTN_SUPPORT = "📞 پشتیبانی"
BTN_ADMIN = "🛠 پنل مدیریت"
BTN_BACK = "🔙 بازگشت"
BTN_HOME = "🏠 منوی اصلی"
BTN_CANCEL = "❌ انصراف"
BTN_ADMIN_STATS_USERS = "📊 آمار کاربران"
BTN_ADMIN_STATS_CHANNELS = "📢 آمار کانال‌ها"
BTN_ADMIN_STATS_NEWS = "📰 آمار اخبار"
BTN_ADMIN_USERS = "👤 مدیریت کاربران"
BTN_ADMIN_CHANNELS = "📺 مدیریت کانال‌ها"
BTN_ADMIN_ADMINS = "👮 ادمین‌ها"
BTN_ADMIN_BROADCAST = "📨 ارسال همگانی"
BTN_ADMIN_SETTINGS = "⚙️ تنظیمات ربات"
BTN_ADMIN_JOIN = "🔒 جوین اجباری"


def main_menu(is_admin=False):
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton(BTN_HOME), row=1)
    keyboard.add(MenuKeyboardButton(BTN_SUPPORT), row=1)
    if is_admin:
        keyboard.add(MenuKeyboardButton(BTN_ADMIN), row=2)
    return keyboard


def home_inline_menu(show_free=True):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⚙️ تنظیمات کانال", callback_data="m_settings"), row=1)
    keyboard.add(InlineKeyboardButton("➕ افزودن کانال", callback_data="m_add"), row=1)
    keyboard.add(InlineKeyboardButton("⏸️ توقف ارسال", callback_data="m_pause"), row=2)
    keyboard.add(InlineKeyboardButton("▶️ شروع ارسال", callback_data="m_resume"), row=2)
    keyboard.add(InlineKeyboardButton("📊 آمار کانال", callback_data="m_stats"), row=3)
    keyboard.add(InlineKeyboardButton("💳 خرید اشتراک", callback_data="m_buy"), row=4)
    keyboard.add(InlineKeyboardButton("🔑 ورود کد لایسنس", callback_data="m_license"), row=5)
    if show_free:
        keyboard.add(InlineKeyboardButton("🎁 اشتراک رایگان ۳ روزه", callback_data="m_free"), row=6)
    keyboard.add(InlineKeyboardButton("📞 پشتیبانی", callback_data="m_support"), row=7)
    return keyboard


def plans_menu():
    keyboard = InlineKeyboardMarkup()
    row = 1
    for key, plan in PLANS.items():
        price = f"{plan['price']:,}".replace(",", "٬")
        keyboard.add(
            InlineKeyboardButton(f"{plan['title']} — {price} تومن", callback_data=f"plan_{key}"),
            row=row,
        )
        row += 1
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_home"), row=row)
    return keyboard


def pay_method_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"), row=1)
    keyboard.add(InlineKeyboardButton("🎁 پاکت هدیه", callback_data="pay_gift"), row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_buy"), row=2)
    return keyboard


def card_pay_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ واریز کردم", callback_data="pay_paid"), row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_buy"), row=2)
    return keyboard


def admin_pay_menu(req_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{req_id}"), row=1)
    keyboard.add(InlineKeyboardButton("❌ رد", callback_data=f"adm_no_{req_id}"), row=1)
    keyboard.add(InlineKeyboardButton("📝 ارسال پیام به کاربر", callback_data=f"adm_msg_{req_id}"), row=2)
    return keyboard


def channel_pick_menu(channels, prefix):
    keyboard = InlineKeyboardMarkup()
    row = 1
    for channel in channels:
        status = "🟢" if channel.get("status") == "active" else "🔴"
        keyboard.add(
            InlineKeyboardButton(f"{status} {channel['id']}", callback_data=f"{prefix}{channel['id']}"),
            row=row,
        )
        row += 1
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_home"), row=row)
    return keyboard


def channel_menu():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton(BTN_ADD_CHANNEL), row=1)
    keyboard.add(MenuKeyboardButton(BTN_BACK), row=2)
    keyboard.add(MenuKeyboardButton(BTN_HOME), row=2)
    return keyboard


def channel_settings_bottom_menu():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton(BTN_BACK), row=1)
    keyboard.add(MenuKeyboardButton(BTN_HOME), row=1)
    return keyboard


def channel_inline_menu(channels):
    keyboard = InlineKeyboardMarkup()
    for channel in channels:
        keyboard.add(InlineKeyboardButton(f"⚙️ {channel['id']}", callback_data=f"channel_{channel['id']}"))
    keyboard.add(InlineKeyboardButton("🔙 منوی اصلی", callback_data="m_home"))
    return keyboard


def channel_settings_menu(channel_id, send_image=True, show_emoji=True):
    image_text = "🖼 عکس: 🟢 روشن" if send_image else "🖼 عکس: 🔴 خاموش"
    emoji_text = "😀 ایموجی: 🟢 روشن" if show_emoji else "😀 ایموجی: 🔴 خاموش"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(image_text, callback_data=f"img_{channel_id}"), row=1)
    keyboard.add(InlineKeyboardButton(emoji_text, callback_data=f"emoji_{channel_id}"), row=1)
    keyboard.add(InlineKeyboardButton("⏱ فاصله ارسال", callback_data=f"time_{channel_id}"), row=2)
    keyboard.add(InlineKeyboardButton("🏷 دسته‌بندی خبر", callback_data=f"cat_{channel_id}"), row=2)
    keyboard.add(InlineKeyboardButton("✏️ متن پایین خبر", callback_data=f"link_{channel_id}"), row=3)
    keyboard.add(InlineKeyboardButton("🗑 حذف کانال", callback_data=f"delete_{channel_id}"), row=3)
    keyboard.add(InlineKeyboardButton("🔙 منوی اصلی", callback_data="m_home"), row=4)
    return keyboard


def delete_channel_menu(channel_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"yesdel_{channel_id}"), row=1)
    keyboard.add(InlineKeyboardButton("❌ انصراف", callback_data=f"nodel_{channel_id}"), row=1)
    return keyboard


def back_menu():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton(BTN_BACK), row=1)
    keyboard.add(MenuKeyboardButton(BTN_HOME), row=1)
    return keyboard


def cancel_menu():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton(BTN_CANCEL), row=1)
    return keyboard


def footer_preview_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ تایید", callback_data="footer_save"), row=1)
    keyboard.add(InlineKeyboardButton("✏️ ویرایش", callback_data="footer_edit"), row=1)
    keyboard.add(InlineKeyboardButton("❌ انصراف", callback_data="footer_cancel"), row=2)
    return keyboard


def footer_manage_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✏️ تغییر متن", callback_data="footer_edit"), row=1)
    keyboard.add(InlineKeyboardButton("🗑 حذف متن", callback_data="footer_delete"), row=1)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="footer_back"), row=2)
    return keyboard


def footer_delete_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ بله، حذف شود", callback_data="footer_delete_yes"), row=1)
    keyboard.add(InlineKeyboardButton("❌ خیر", callback_data="footer_delete_no"), row=1)
    return keyboard


def category_menu(selected=None, locked=None):
    selected = selected or []
    locked = set(locked or [])
    def label(name, text):
        if name in locked:
            return f"🔒 {text}"
        return f"✅ {text}" if name in selected else text
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(label("جنگ", "🚨 جنگ"), callback_data="cat_select_جنگ"), row=1)
    keyboard.add(InlineKeyboardButton(label("آب‌وهوا", "🌬 آب‌وهوا"), callback_data="cat_select_آب‌وهوا"), row=1)
    keyboard.add(InlineKeyboardButton(label("اقتصاد", "💵 اقتصاد"), callback_data="cat_select_اقتصاد"), row=2)
    keyboard.add(InlineKeyboardButton(label("فناوری", "💻 فناوری"), callback_data="cat_select_فناوری"), row=2)
    keyboard.add(InlineKeyboardButton(label("ورزش", "⚽ ورزش"), callback_data="cat_select_ورزش"), row=3)
    keyboard.add(InlineKeyboardButton(label("سیاسی", "🏛 سیاسی"), callback_data="cat_select_سیاسی"), row=3)
    keyboard.add(InlineKeyboardButton(label("همه", "🌍 همه دسته‌ها"), callback_data="cat_select_همه"), row=4)
    keyboard.add(InlineKeyboardButton("💾 ذخیره دسته‌ها", callback_data="cat_save"), row=5)
    return keyboard


def send_time_menu(channel_id, locked=None):
    locked = set(locked or [])
    def label(minutes, text):
        return f"🔒 {text}" if minutes in locked else text
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(label(1, "🕐 ۱ دقیقه"), callback_data=f"stime_1_{channel_id}"), row=1)
    keyboard.add(InlineKeyboardButton(label(5, "🕔 ۵ دقیقه"), callback_data=f"stime_5_{channel_id}"), row=1)
    keyboard.add(InlineKeyboardButton("🕙 ۱۰ دقیقه", callback_data=f"stime_10_{channel_id}"), row=2)
    keyboard.add(InlineKeyboardButton("🕒 ۱۵ دقیقه", callback_data=f"stime_15_{channel_id}"), row=2)
    keyboard.add(InlineKeyboardButton("🕞 ۳۰ دقیقه", callback_data=f"stime_30_{channel_id}"), row=3)
    keyboard.add(InlineKeyboardButton("🕐 ۶۰ دقیقه", callback_data=f"stime_60_{channel_id}"), row=3)
    return keyboard


def admin_menu():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_STATS_USERS), row=1)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_STATS_CHANNELS), row=2)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_STATS_NEWS), row=3)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_USERS), row=4)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_CHANNELS), row=5)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_ADMINS), row=6)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_BROADCAST), row=7)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_SETTINGS), row=8)
    keyboard.add(MenuKeyboardButton(BTN_ADMIN_JOIN), row=9)
    keyboard.add(MenuKeyboardButton("🔙 بازگشت"), row=10)
    return keyboard


def pagination_menu(page, total_pages, prefix):
    keyboard = InlineKeyboardMarkup()
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}_{page-1}"))
    buttons.append(InlineKeyboardButton(f"📄 {page+1} / {total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}_{page+1}"))
    keyboard.add(*buttons, row=1)
    return keyboard
