from __future__ import annotations

from datetime import date
from typing import Literal

from database.postgres import get_pool


StatName = Literal[
    "messages",
    "gifs",
    "voice",
    "photos",
    "videos",
    "other",
]


async def upsert_user(
    user_id: int,
    username: str | None,
    display_name: str,
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO users (
            user_id,
            username,
            display_name
        )
        VALUES ($1, $2, $3)

        ON CONFLICT (user_id)
        DO UPDATE SET
            username = EXCLUDED.username,
            display_name = EXCLUDED.display_name,
            last_seen = NOW()
        """,
        user_id,
        username,
        display_name,
    )


async def register_group_member(
    group_id: int,
    user_id: int,
    role: str = "member",
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO group_members (
            group_id,
            user_id,
            role
        )
        VALUES ($1, $2, $3)

        ON CONFLICT (group_id, user_id)
        DO UPDATE SET
            role = EXCLUDED.role
        """,
        group_id,
        user_id,
        role,
    )


async def increment_stat(
    group_id: int,
    user_id: int,
    stat: StatName,
    day: date,
) -> None:
    allowed: set[str] = {
        "messages",
        "gifs",
        "voice",
        "photos",
        "videos",
        "other",
    }

    if stat not in allowed:
        raise ValueError(f"Invalid statistic: {stat}")

    pool = get_pool()

    query = f"""
        INSERT INTO daily_stats (
            group_id,
            user_id,
            date,
            {stat}
        )
        VALUES ($1, $2, $3, 1)

        ON CONFLICT (
            group_id,
            user_id,
            date
        )
        DO UPDATE SET
            {stat} = daily_stats.{stat} + 1
    """

    await pool.execute(
        query,
        group_id,
        user_id,
        day,
    )


async def count_learned_words(
    group_id: int,
) -> int:
    pool = get_pool()

    result = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM learned_words
        WHERE group_id = $1
        """,
        group_id,
    )

    return int(result or 0)


async def get_daily_user_stats(
    group_id: int,
    user_id: int,
    day: date,
):
    pool = get_pool()

    return await pool.fetchrow(
        """
        SELECT
            messages,
            gifs,
            voice,
            photos,
            videos,
            other
        FROM daily_stats
        WHERE
            group_id = $1
            AND user_id = $2
            AND date = $3
        """,
        group_id,
        user_id,
        day,
    )


async def get_group_daily_stats(
    group_id: int,
    day: date,
):
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
        WHERE
            group_id = $1
            AND date = $2
        """,
        group_id,
        day,
    )


async def get_top_active_users(
    group_id: int,
    day: date,
    limit: int = 10,
):
    pool = get_pool()

    return await pool.fetch(
        """
        SELECT
            u.user_id,
            u.username,
            u.display_name,
            COALESCE(ds.messages, 0) AS messages
        FROM daily_stats ds

        JOIN users u
            ON u.user_id = ds.user_id

        WHERE
            ds.group_id = $1
            AND ds.date = $2

        ORDER BY
            ds.messages DESC,
            u.user_id ASC

        LIMIT $3
        """,
        group_id,
        day,
        limit,
    )
