from bale import Message, CallbackQuery
from client import bot

from users import load_users
from keyboards import pagination_menu

from datetime import datetime


# ==========================
# دریافت همه کانال‌ها
# ==========================

def get_all_channels():

    users = load_users()

    channels = []

    for user_id, user in users.items():

        for channel in user.get("channels", []):

            channels.append({
                "id": channel["id"],
                "user_id": user_id
            })

    return channels


# ==========================
# ساخت صفحه آمار کانال‌ها
# ==========================

def build_channels_page(page=0):

    channels = get_all_channels()

    per_page = 30

    total_pages = max(
        1,
        (len(channels) + per_page - 1) // per_page
    )

    start = page * per_page
    end = start + per_page

    text = (
        "📢 آمار کانال‌ها\n\n"
        f"📺 تعداد کل کانال‌ها: {len(channels)}\n\n"
        "━━━━━━━━━━━━━━\n\n"
    )

    for index, channel in enumerate(
        channels[start:end],
        start=start + 1
    ):

        text += (
            f"{index}. {channel['id']}\n"
            f"└ 👤 افزوده شده توسط: {channel['user_id']}\n\n"
        )

    return text, total_pages



# ==========================
# پنل مدیریت
# ==========================

@bot.event
async def on_message(message: Message):

    if message.from_user is None:
        return


    # ==========================
    # آمار کاربران
    # ==========================

    if message.content == "📊 آمار کاربران":

        users = load_users()

        total_users = len(users)

        today = datetime.utcnow().strftime("%Y-%m-%d")

        today_users = 0

        for user in users.values():

            join_date = user.get("join_date", "")

            if join_date.startswith(today):
                today_users += 1


        await message.reply(
            "📊 آمار کاربران\n\n"
            f"👤 تعداد کل کاربران: {total_users}\n"
            f"🆕 کاربران جدید امروز: {today_users}"
        )

        return



    # ==========================
    # آمار کانال‌ها
    # ==========================

    if message.content == "📢 آمار کانال‌ها":

        text, total_pages = build_channels_page(0)

        await message.reply(
            text,
            components=pagination_menu(
                0,
                total_pages,
                "channel_stats"
            )
        )

        return



# ==========================
# دکمه های صفحه بندی آمار کانال ها
# ==========================

@bot.event
async def on_callback_query(query: CallbackQuery):

    data = query.data

    if data.startswith("channel_stats_"):

        page = int(data.split("_")[-1])

        text, total_pages = build_channels_page(page)

        await query.message.edit(
            text,
            components=pagination_menu(
                page,
                total_pages,
                "channel_stats"
            )
        )

        return