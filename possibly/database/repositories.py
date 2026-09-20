# POSSIBLY
# PostgreSQL repositories

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from database.postgres import get_pool


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────

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


async def get_user(user_id: int) -> dict[str, Any] | None:
    pool = get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            user_id,
            username,
            display_name,
            first_seen,
            last_seen
        FROM users
        WHERE user_id = $1
        """,
        user_id,
    )

    return dict(row) if row else None


# ─────────────────────────────────────────────
# Group members
# ─────────────────────────────────────────────

async def upsert_group_member(
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


async def get_member_role(
    group_id: int,
    user_id: int,
) -> str | None:
    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT role
        FROM group_members
        WHERE group_id = $1
          AND user_id = $2
        """,
        group_id,
        user_id,
    )


async def get_group_members(
    group_id: int,
) -> list[dict[str, Any]]:
    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            gm.user_id,
            gm.role,
            gm.joined_at,
            u.username,
            u.display_name
        FROM group_members gm

        LEFT JOIN users u
            ON u.user_id = gm.user_id

        WHERE gm.group_id = $1

        ORDER BY
            CASE gm.role
                WHEN 'owner' THEN 0
                WHEN 'admin' THEN 1
                ELSE 2
            END,
            u.display_name
        """,
        group_id,
    )

    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# Learning system
# ─────────────────────────────────────────────

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


async def add_learned_word(
    group_id: int,
    trigger: str,
    response: str,
    created_by: int,
) -> bool:
    pool = get_pool()

    current_count = await count_learned_words(group_id)

    if current_count >= 300:
        return False

    result = await pool.execute(
        """
        INSERT INTO learned_words (
            group_id,
            trigger,
            response,
            created_by
        )
        VALUES ($1, $2, $3, $4)

        ON CONFLICT (group_id, trigger)
        DO UPDATE SET
            response = EXCLUDED.response,
            created_by = EXCLUDED.created_by,
            created_at = NOW()
        """,
        group_id,
        trigger,
        response,
        created_by,
    )

    return result.startswith("INSERT")


async def get_learned_response(
    group_id: int,
    trigger: str,
) -> str | None:
    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT response
        FROM learned_words
        WHERE group_id = $1
          AND trigger = $2
        """,
        group_id,
        trigger,
    )


async def delete_learned_word(
    group_id: int,
    trigger: str,
) -> bool:
    pool = get_pool()

    result = await pool.execute(
        """
        DELETE FROM learned_words
        WHERE group_id = $1
          AND trigger = $2
        """,
        group_id,
        trigger,
    )

    return result.endswith("1")


async def list_learned_words(
    group_id: int,
) -> list[dict[str, Any]]:
    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            id,
            trigger,
            response,
            created_by,
            created_at
        FROM learned_words
        WHERE group_id = $1
        ORDER BY id ASC
        """,
        group_id,
    )

    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# Daily statistics
# ─────────────────────────────────────────────

_ALLOWED_STATS = {
    "messages",
    "gifs",
    "voice",
    "photos",
    "videos",
    "other",
}


async def increment_stat(
    group_id: int,
    user_id: int,
    stat: str,
    day: date | None = None,
) -> None:
    if stat not in _ALLOWED_STATS:
        raise ValueError(f"Invalid statistic: {stat}")

    if day is None:
        day = datetime.now(timezone.utc).date()

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
            {stat} = daily_stats.{stat} + 1
        """,
        group_id,
        user_id,
        day,
    )


async def get_user_daily_stats(
    group_id: int,
    user_id: int,
    day: date | None = None,
) -> dict[str, int]:
    if day is None:
        day = datetime.now(timezone.utc).date()

    pool = get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            messages,
            gifs,
            voice,
            photos,
            videos,
            other
        FROM daily_stats
        WHERE group_id = $1
          AND user_id = $2
          AND date = $3
        """,
        group_id,
        user_id,
        day,
    )

    if not row:
        return {
            "messages": 0,
            "gifs": 0,
            "voice": 0,
            "photos": 0,
            "videos": 0,
            "other": 0,
        }

    return dict(row)


async def get_group_daily_stats(
    group_id: int,
    day: date | None = None,
) -> dict[str, int]:
    if day is None:
        day = datetime.now(timezone.utc).date()

    pool = get_pool()

    row = await pool.fetchrow(
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

    return dict(row)


async def get_top_active_users(
    group_id: int,
    day: date | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    if day is None:
        day = datetime.now(timezone.utc).date()

    limit = max(1, min(limit, 20))

    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            ds.user_id,
            ds.messages,
            u.username,
            u.display_name
        FROM daily_stats ds

        LEFT JOIN users u
            ON u.user_id = ds.user_id

        WHERE ds.group_id = $1
          AND ds.date = $2

        ORDER BY
            ds.messages DESC,
            ds.user_id ASC

        LIMIT $3
        """,
        group_id,
        day,
        limit,
    )

    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# Games
# ─────────────────────────────────────────────

async def create_game(
    game_id: UUID,
    group_id: int,
    game_type: str,
    creator_id: int,
    status: str,
    state: dict[str, Any] | None = None,
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO games (
            game_id,
            group_id,
            type,
            creator_id,
            status,
            state
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5,
            COALESCE($6::jsonb, '{}'::jsonb)
        )
        """,
        game_id,
        group_id,
        game_type,
        creator_id,
        status,
        state,
    )


async def get_game(
    game_id: UUID,
) -> dict[str, Any] | None:
    pool = get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            game_id,
            group_id,
            type,
            creator_id,
            status,
            state,
            created_at,
            updated_at
        FROM games
        WHERE game_id = $1
        """,
        game_id,
    )

    return dict(row) if row else None


async def update_game(
    game_id: UUID,
    *,
    status: str | None = None,
    state: dict[str, Any] | None = None,
) -> None:
    pool = get_pool()

    if status is not None and state is not None:
        await pool.execute(
            """
            UPDATE games
            SET
                status = $2,
                state = $3::jsonb,
                updated_at = NOW()
            WHERE game_id = $1
            """,
            game_id,
            status,
            state,
        )

    elif status is not None:
        await pool.execute(
            """
            UPDATE games
            SET
                status = $2,
                updated_at = NOW()
            WHERE game_id = $1
            """,
            game_id,
            status,
        )

    elif state is not None:
        await pool.execute(
            """
            UPDATE games
            SET
                state = $2::jsonb,
                updated_at = NOW()
            WHERE game_id = $1
            """,
            game_id,
            state,
        )


async def add_game_player(
    game_id: UUID,
    user_id: int,
    state: dict[str, Any] | None = None,
) -> bool:
    pool = get_pool()

    result = await pool.execute(
        """
        INSERT INTO game_players (
            game_id,
            user_id,
            state
        )
        VALUES (
            $1,
            $2,
            COALESCE($3::jsonb, '{}'::jsonb)
        )

        ON CONFLICT (
            game_id,
            user_id
        )
        DO NOTHING
        """,
        game_id,
        user_id,
        state,
    )

    return result.startswith("INSERT")


async def get_game_players(
    game_id: UUID,
) -> list[dict[str, Any]]:
    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            user_id,
            state,
            joined_at
        FROM game_players
        WHERE game_id = $1
        ORDER BY joined_at ASC
        """,
        game_id,
    )

    return [dict(row) for row in rows]


async def remove_game_player(
    game_id: UUID,
    user_id: int,
) -> bool:
    pool = get_pool()

    result = await pool.execute(
        """
        DELETE FROM game_players
        WHERE game_id = $1
          AND user_id = $2
        """,
        game_id,
        user_id,
    )

    return result.endswith("1")


# ─────────────────────────────────────────────
# Whispers
# ─────────────────────────────────────────────

async def create_whisper(
    group_id: int,
    sender_id: int,
    receiver_id: int,
    content: str,
    expires_at: datetime | None = None,
) -> int:
    pool = get_pool()

    return int(
        await pool.fetchval(
            """
            INSERT INTO whispers (
                group_id,
                sender_id,
                receiver_id,
                encrypted_or_private_content,
                expires_at
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            group_id,
            sender_id,
            receiver_id,
            content,
            expires_at,
        )
    )


async def get_whisper(
    whisper_id: int,
) -> dict[str, Any] | None:
    pool = get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            id,
            group_id,
            sender_id,
            receiver_id,
            encrypted_or_private_content,
            created_at,
            expires_at,
            viewed
        FROM whispers
        WHERE id = $1
        """,
        whisper_id,
    )

    return dict(row) if row else None


async def mark_whisper_viewed(
    whisper_id: int,
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        UPDATE whispers
        SET viewed = TRUE
        WHERE id = $1
        """,
        whisper_id,
    )


async def count_recent_whispers(
    sender_id: int,
    since: datetime,
) -> int:
    pool = get_pool()

    result = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM whispers
        WHERE sender_id = $1
          AND created_at >= $2
        """,
        sender_id,
        since,
    )

    return int(result or 0)


# ─────────────────────────────────────────────
# Moderation logs
# ─────────────────────────────────────────────

async def create_moderation_log(
    group_id: int,
    actor_id: int,
    action: str,
    target_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO moderation_logs (
            group_id,
            actor_id,
            target_id,
            action,
            details
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            COALESCE($5::jsonb, '{}'::jsonb)
        )
        """,
        group_id,
        actor_id,
        target_id,
        action,
        details,
    )


async def get_moderation_logs(
    group_id: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 200))

    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            id,
            actor_id,
            target_id,
            action,
            details,
            created_at
        FROM moderation_logs
        WHERE group_id = $1
        ORDER BY id DESC
        LIMIT $2
        """,
        group_id,
        limit,
    )

    return [dict(row) for row in rows]
