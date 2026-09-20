# POSSIBLY
# Statistics handler

from __future__ import annotations

import logging
from datetime import date

from bot.messages import stats as stats_message
from database.repositories import (
    get_daily_user_stats,
    get_group_daily_stats,
    get_top_active_users,
    upsert_user,
    increment_stat,
)


logger = logging.getLogger("POSSIBLY.stats")


def register(bot) -> None:
    """
    Statistics handler registration point.

    The Bale-specific event decorator will be connected after
    verifying the installed python-bale-bot API.
    """

    logger.info("Statistics handler registered")


def _user_display_name(row) -> str:
    username = row["username"]

    if username:
        return f"@{username.lstrip('@')}"

    display_name = row["display_name"]

    if display_name:
        return display_name

    return str(row["user_id"])


async def record_message(
    user_id: int,
    username: str | None,
    display_name: str,
    group_id: int,
    stat_type: str = "other",
) -> None:
    """
    Register a user and increment today's statistic.

    stat_type:
        messages
        gifs
        voice
        photos
        videos
        other
    """

    await upsert_user(
        user_id=user_id,
        username=username,
        display_name=display_name,
    )

    await increment_stat(
        group_id=group_id,
        user_id=user_id,
        stat="messages",
        day=date.today(),
    )

    if stat_type != "messages":
        await increment_stat(
            group_id=group_id,
            user_id=user_id,
            stat=stat_type,
            day=date.today(),
        )


async def build_my_stats(
    group_id: int,
    user_id: int,
) -> str:
    today = date.today()

    row = await get_daily_user_stats(
        group_id=group_id,
        user_id=user_id,
        day=today,
    )

    if row is None:
        return stats_message(
            "آمار امروز شما هنوز ثبت نشده است.\n\n"
            "💬 پیام‌ها: 0\n"
            "🎞 GIF: 0\n"
            "🎤 Voice: 0\n"
            "🖼 عکس: 0\n"
            "🎬 ویدیو: 0\n"
            "📦 سایر: 0"
        )

    return stats_message(
        "آمار امروز شما\n\n"
        f"💬 پیام‌ها: {row['messages']}\n"
        f"🎞 GIF: {row['gifs']}\n"
        f"🎤 Voice: {row['voice']}\n"
        f"🖼 عکس: {row['photos']}\n"
        f"🎬 ویدیو: {row['videos']}\n"
        f"📦 سایر: {row['other']}"
    )


async def build_group_stats(
    group_id: int,
) -> str:
    today = date.today()

    totals = await get_group_daily_stats(
        group_id=group_id,
        day=today,
    )

    top_users = await get_top_active_users(
        group_id=group_id,
        day=today,
        limit=3,
    )

    if totals is None:
        totals = {
            "messages": 0,
            "gifs": 0,
            "voice": 0,
            "photos": 0,
            "videos": 0,
            "other": 0,
        }

    lines = [
        "آمار امروز",
        "",
        f"💬 پیام‌ها: {totals['messages']}",
        f"🎞 GIF: {totals['gifs']}",
        f"🎤 Voice: {totals['voice']}",
        f"🖼 عکس: {totals['photos']}",
        f"🎬 ویدیو: {totals['videos']}",
        f"📦 سایر: {totals['other']}",
        "",
        "🏆 فعال‌ترین اعضا:",
    ]

    medals = ("🥇", "🥈", "🥉")

    if not top_users:
        lines.append("هنوز آماری ثبت نشده است.")
    else:
        for index, user in enumerate(top_users):
            name = _user_display_name(user)

            lines.append(
                f"{medals[index]} {name} — "
                f"{user['messages']} پیام"
            )

    return stats_message(
        "\n".join(lines)
    )
