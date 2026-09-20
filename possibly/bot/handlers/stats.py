# bot/handlers/stats.py

import logging
from datetime import date

from bale import Bot, Message

from config import settings
from bot.messages import info
from database.postgres import get_pool
from database.repositories import increment_stat, upsert_user

logger = logging.getLogger("POSSIBLY.stats")


def get_user(message: Message):
    author = getattr(message, "author", None)

    if author is None:
        return None

    user_id = getattr(author, "id", None)

    if user_id is None:
        return None

    username = getattr(author, "username", None)
    display_name = getattr(author, "first_name", None)

    if not display_name:
        display_name = getattr(author, "name", None)

    if not display_name:
        display_name = username or str(user_id)

    return (
        int(user_id),
        username,
        str(display_name),
    )


def detect_stat(message: Message) -> str:
    """
    تشخیص نوع محتوای پیام.

    messages همیشه برای هر پیام ثبت می‌شود.
    نوع محتوای خاص نیز جداگانه شمارش می‌شود.
    """

    if getattr(message, "gif", None) is not None:
        return "gifs"

    if getattr(message, "voice", None) is not None:
        return "voice"

    if getattr(message, "photo", None) is not None:
        return "photos"

    if getattr(message, "video", None) is not None:
        return "videos"

    return "other"


async def get_group_stats(group_id: int, day: date):
    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            u.user_id,
            u.username,
            u.display_name,
            ds.messages,
            ds.gifs,
            ds.voice,
            ds.photos,
            ds.videos,
            ds.other
        FROM daily_stats ds
        LEFT JOIN users u
            ON u.user_id = ds.user_id
        WHERE ds.group_id = $1
          AND ds.date = $2
        ORDER BY ds.messages DESC
        """,
        group_id,
        day,
    )

    return rows


async def get_group_totals(group_id: int, day: date):
    pool = get_pool()

    return await pool.fetchrow(
        """
        SELECT
            COALESCE(SUM(messages), 0) AS messages,
            COALESCE(SUM(gifs), 0) AS gifs,
            COALESCE(SUM(voice), 0) AS voice,
            COALESCE(SUM(photos), 0) AS photos,
            COALESCE(SUM(videos), 0) AS videos,
            COALESCE(SUM(other), 0) AS other
        FROM daily_stats
        WHERE group_id = $1
          AND date = $2
        """,
        group_id,
        day,
    )


async def get_registered_members(group_id: int) -> int:
    pool = get_pool()

    result = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM group_members
        WHERE group_id = $1
        """,
        group_id,
    )

    return int(result or 0)


async def record_message(
    message: Message,
    group_id: int,
):
    user = get_user(message)

    if user is None:
        return

    user_id, username, display_name = user

    await upsert_user(
        user_id=user_id,
        username=username,
        display_name=display_name,
    )

    today = date.today()

    await increment_stat(
        group_id=group_id,
        user_id=user_id,
        stat="messages",
        day=today,
    )

    stat = detect_stat(message)

    await increment_stat(
        group_id=group_id,
        user_id=user_id,
        stat=stat,
        day=today,
    )


def format_user_name(row) -> str:
    username = row["username"]
    display_name = row["display_name"]

    if username:
        return f"@{username}"

    if display_name:
        return display_name

    return str(row["user_id"])


async def send_stats(message: Message, group_id: int):
    today = date.today()

    totals = await get_group_totals(
        group_id,
        today,
    )

    rows = await get_group_stats(
        group_id,
        today,
    )

    registered_members = await get_registered_members(
        group_id
    )

    lines = [
        "📊 آمار امروز",
        "",
        f"👥 اعضای ثبت‌شده: {registered_members}",
        f"💬 پیام‌ها: {totals['messages']}",
        f"🎞 GIF: {totals['gifs']}",
        f"🎤 Voice: {totals['voice']}",
        f"🖼 عکس: {totals['photos']}",
        f"🎬 ویدیو: {totals['videos']}",
        "",
        "🏆 فعال‌ترین اعضا:",
    ]

    if not rows:
        lines.append(
            "هنوز آماری برای امروز ثبت نشده است."
        )
    else:
        medals = ["🥇", "🥈", "🥉"]

        for index, row in enumerate(rows[:3]):
            name = format_user_name(row)

            lines.append(
                f"{medals[index]} {name} — "
                f"{row['messages']} پیام"
            )

    await message.reply(
        info("\n".join(lines))
    )


def register_stats_handlers(bot: Bot):

    @bot.event
    async def on_message(message: Message):

        try:
            chat = getattr(message, "chat", None)

            if chat is None:
                return

            group_id = getattr(chat, "id", None)

            if group_id is None:
                return

            group_id = int(group_id)

            if group_id != settings.ALLOWED_GROUP_ID:
                return

            text = getattr(message, "content", None)

            if not text:
                text = getattr(message, "text", None)

            text = (text or "").strip()

            # دستور آمار
            if text in ("امار", "آمار"):

                await send_stats(
                    message,
                    group_id,
                )

                return

            # ثبت آمار پیام
            await record_message(
                message,
                group_id,
            )

        except Exception:
            logger.exception(
                "Statistics handler failed"
            )
