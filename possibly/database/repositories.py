from datetime import date

from database.postgres import get_pool


async def upsert_user(
    user_id: int,
    username: str | None,
    display_name: str,
):
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


async def increment_stat(
    group_id: int,
    user_id: int,
    stat: str,
    day: date,
):
    allowed = {
        "messages",
        "gifs",
        "voice",
        "photos",
        "videos",
        "other",
    }

    if stat not in allowed:
        raise ValueError("Invalid statistic")

    pool = get_pool()

    await pool.execute(
        f"""
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
            {stat} =
                daily_stats.{stat} + 1
        """,
        group_id,
        user_id,
        day,
    )


async def count_learned_words(group_id: int) -> int:
    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM learned_words
        WHERE group_id = $1
        """,
        group_id,
    )
